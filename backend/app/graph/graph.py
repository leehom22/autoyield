"""
ai_assistant_graph.py — AI Assistant (fixed)

Fixes from original:
1. executor_node bound tools but never had a path to actually EXECUTE them.
   If the executor's LLM decided to call execute_operational_action, those tool_calls
   were returned in the AIMessage but never run — there was no edge from executor to tool_node.
   Fixed: executor now has its own conditional edge to tool_node, with tool_node routing
   back to executor (not supervisor) so the executor interprets the result.
2. debate_rounds increment was in p_agent_node but the check was only in route_after_r_agent.
   Added safety: if debate_rounds >= 3 AND no consensus, R-Agent is forced to concede
   so the graph always terminates.
3. Supervisor debate detection was purely keyword-based on the user message.
   Added a secondary check: if the supervisor's LLM response itself mentions debate
   keywords, also trigger debate. Reduces false negatives.
"""

import os
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools.mcp_tools_call import get_all_lc_tools

load_dotenv()


# ─────────────────────────────────────────────
# GLM client
# ─────────────────────────────────────────────
def get_glm():
    return ChatOpenAI(
        model=os.getenv("GLM_MODEL", "glm-4-plus"),
        api_key=os.getenv("GLM_API_KEY"),
        base_url=os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
        temperature=0.3,
    )


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    p_agent_position: str
    r_agent_position: str
    debate_rounds: int
    consensus_reached: bool
    requires_human_approval: bool
    decision_type: str
    # Tracks which node tool_node should return to
    pending_handler: Literal["supervisor", "executor", "none"]
    final_response: str


# ─────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────
SUPERVISOR_PROMPT = """You are the AutoYield Restaurant AI Supervisor.
Your job is to:
1. Understand the operator's instruction or query.
2. Decide if this requires a P-Agent vs R-Agent debate:
   Trigger debate for: price changes >10%, spending >RM200, menu restructuring,
   supplier switching, flash sale, bulk purchase, or any promotion.
3. Handle directly for: simple queries, read-only requests, small inventory adjustments.

Available tools let you read inventory, finance, and ops data.
Always check business state before making decisions.
For high-stakes actions (spending >RM500, price change >15%), use send_human_notification first."""

P_AGENT_PROMPT = """You are the P-Agent (Profit Maximization Agent) in a dual-agent debate.
Your role: argue for the boldest profitable action. Maximize revenue and margin.
- Use simulate_yield_scenario to quantify the upside with real numbers.
- Propose specific actions: which item, what price, what discount, projected revenue.
- Challenge conservative thinking with data.
Keep your position to 2-3 sentences with specific RM figures."""

R_AGENT_PROMPT = """You are the R-Agent (Risk Mitigation Agent) in a dual-agent debate.
Your role: stress-test the P-Agent's proposal. Identify the single most critical risk.
- Use check_operational_capacity to validate feasibility before agreeing to anything.
- Question P-Agent's assumptions with specific counter-data.
- Propose a guardrail (cap, staged rollout, approval gate) rather than outright rejection.

If the P-Agent's numbers are solid and the risk is manageable, concede:
Start your reply with 'CONSENSUS: ' followed by the agreed position.
Keep your position to 2-3 sentences."""

EXECUTOR_PROMPT = """You are the AutoYield Executor. Your job is to take a decision and run it.
You have access to all write tools. Execute the agreed decision now using the appropriate tools.
If spending > RM500 or price change > 15%, use send_human_notification instead of executing directly.
After execution, summarize: what was done, transaction ID, expected outcome."""


# ─────────────────────────────────────────────
# Debate trigger keywords
# ─────────────────────────────────────────────
_DEBATE_TRIGGERS = [
    "price change", "promotion", "supplier switch", "flash sale",
    "menu restructure", "bulk purchase", "discount", "voucher",
    "ad boost", "campaign", "increase price", "reduce price",
]


# ─────────────────────────────────────────────
# Node: Supervisor
# ─────────────────────────────────────────────
def supervisor_node(state: AgentState) -> AgentState:
    tools = get_all_lc_tools()
    llm = get_glm().bind_tools(tools)

    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    # Keyword check on user message
    last_user_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content.lower()
            break

    needs_debate = any(trigger in last_user_msg for trigger in _DEBATE_TRIGGERS)

    # Secondary check: supervisor's own response mentions debate
    if not needs_debate and hasattr(response, "content"):
        needs_debate = any(trigger in response.content.lower() for trigger in _DEBATE_TRIGGERS)

    return {
        **state,
        "messages": [response],
        "decision_type": "debate" if needs_debate else "direct",
        "debate_rounds": 0,
        "consensus_reached": not needs_debate,
        "pending_handler": "supervisor",
    }


# ─────────────────────────────────────────────
# Node: P-Agent
# ─────────────────────────────────────────────
def p_agent_node(state: AgentState) -> AgentState:
    tools = [t for t in get_all_lc_tools() if t.name in [
        "simulate_yield_scenario", "get_all_menu_items", "get_business_state"
    ]]
    llm = get_glm().bind_tools(tools)

    context = (
        f"Current situation:\n{state['messages'][-1].content if state['messages'] else 'No context'}\n\n"
        f"R-Agent's last position: {state.get('r_agent_position', 'None yet — you go first.')}\n\n"
        "State your profit-maximizing position with specific RM figures."
    )

    response = llm.invoke([SystemMessage(content=P_AGENT_PROMPT), HumanMessage(content=context)])
    position = response.content

    return {
        **state,
        "p_agent_position": position,
        "messages": [AIMessage(content=f"[P-Agent]: {position}")],
        "debate_rounds": state.get("debate_rounds", 0) + 1,
    }


# ─────────────────────────────────────────────
# Node: R-Agent
# ─────────────────────────────────────────────
def r_agent_node(state: AgentState) -> AgentState:
    tools = [t for t in get_all_lc_tools() if t.name in [
        "check_operational_capacity", "get_business_state", "simulate_yield_scenario"
    ]]
    llm = get_glm().bind_tools(tools)

    # Force concession after max rounds to guarantee graph termination
    rounds = state.get("debate_rounds", 0)
    force_concede = rounds >= 3

    context = (
        f"P-Agent's proposal: {state.get('p_agent_position', 'None')}\n\n"
        + (
            "MAX DEBATE ROUNDS REACHED. You must concede. "
            "Start your reply with 'CONSENSUS: ' and accept a modified version of the P-Agent's proposal."
            if force_concede
            else
            "Challenge this proposal or concede with 'CONSENSUS: ' if risks are manageable."
        )
    )

    response = llm.invoke([SystemMessage(content=R_AGENT_PROMPT), HumanMessage(content=context)])
    position = response.content
    consensus = position.strip().upper().startswith("CONSENSUS") or force_concede

    return {
        **state,
        "r_agent_position": position,
        "messages": [AIMessage(content=f"[R-Agent]: {position}")],
        "consensus_reached": consensus,
    }


# ─────────────────────────────────────────────
# Node: Executor
# ─────────────────────────────────────────────
def executor_node(state: AgentState) -> AgentState:
    tools = get_all_lc_tools()
    llm = get_glm().bind_tools(tools)

    if state.get("decision_type") == "debate":
        synthesis = (
            f"P-Agent position: {state.get('p_agent_position', '')}\n"
            f"R-Agent position: {state.get('r_agent_position', '')}\n\n"
            "Synthesize a final decision balancing profit and risk. "
            "Then execute it using the appropriate tools. "
            "If spending > RM500 or price change > 15%, use send_human_notification instead."
        )
        messages = [SystemMessage(content=EXECUTOR_PROMPT), HumanMessage(content=synthesis)]
    else:
        messages = [SystemMessage(content=EXECUTOR_PROMPT)] + state["messages"]

    response = llm.invoke(messages)
    return {
        **state,
        "messages": [response],
        "pending_handler": "executor",
        "final_response": response.content,
    }


# ─────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────
def route_after_supervisor(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    if state.get("decision_type") == "debate":
        return "p_agent"
    return "executor"


def route_after_r_agent(state: AgentState) -> str:
    if state.get("consensus_reached") or state.get("debate_rounds", 0) >= 3:
        return "executor"
    return "p_agent"


def route_after_executor(state: AgentState) -> str:
    """
    KEY FIX: Executor can call tools (e.g. execute_operational_action).
    If it does, route to tool_node. Otherwise done.
    """
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END


def route_after_tools(state: AgentState) -> str:
    """
    Routes tool_node back to whoever called it.
    Supervisor tool results → supervisor interprets them.
    Executor tool results → executor interprets them (e.g. sees transaction_id).
    """
    handler = state.get("pending_handler", "supervisor")
    if handler == "executor":
        return "executor"
    return "supervisor"


# ─────────────────────────────────────────────
# Build graph
# ─────────────────────────────────────────────
def build_graph():
    tools = get_all_lc_tools()
    tool_node = ToolNode(tools)

    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("p_agent",    p_agent_node)
    builder.add_node("r_agent",    r_agent_node)
    builder.add_node("executor",   executor_node)
    builder.add_node("tool_node",  tool_node)

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges("supervisor", route_after_supervisor, {
        "tool_node": "tool_node",
        "p_agent":   "p_agent",
        "executor":  "executor",
    })

    builder.add_edge("p_agent", "r_agent")

    builder.add_conditional_edges("r_agent", route_after_r_agent, {
        "p_agent":  "p_agent",
        "executor": "executor",
    })

    # KEY FIX: executor can now reach tool_node
    builder.add_conditional_edges("executor", route_after_executor, {
        "tool_node": "tool_node",
        END:         END,
    })

    # KEY FIX: tool_node returns to correct caller
    builder.add_conditional_edges("tool_node", route_after_tools, {
        "supervisor": "supervisor",
        "executor":   "executor",
    })

    return builder.compile()


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph   