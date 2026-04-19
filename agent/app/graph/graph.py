"""
graph/agent_graph.py — LangGraph dual-agent kernel

Architecture:
  user_input → supervisor → [p_agent ↔ r_agent debate] → executor → response

P-Agent (Profit Agent): maximizes revenue, pushes for bold action
R-Agent (Risk Agent):   minimizes downside, challenges P-Agent's logic
Supervisor:             routes input, decides if debate is needed
Executor:               calls MCP tools based on agreed decision
"""
import os
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Import MCP tools as LangChain-compatible tools
from app.tools.mcp_tools_call import get_all_lc_tools

load_dotenv()

# ─────────────────────────────────────────────
# GLM client (OpenAI-compatible)
# ─────────────────────────────────────────────
def get_glm():
    return ChatOpenAI(
        model=os.getenv("GLM_MODEL", "glm-4-plus"),
        api_key=os.getenv("GLM_API_KEY"),
        base_url=os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
        temperature=0.3,
    )


# ─────────────────────────────────────────────
# Graph state
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # Debate state
    p_agent_position: str
    r_agent_position: str
    debate_rounds: int
    consensus_reached: bool
    # Decision metadata
    requires_human_approval: bool
    decision_type: str
    # Final
    final_response: str


# ─────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────
SUPERVISOR_PROMPT = """You are the AutoYield Restaurant AI Supervisor.
Your job is to:
1. Understand the operator's instruction or query
2. Decide if this requires a P-Agent vs R-Agent debate (big decisions: price changes >10%, spending >RM200, menu restructuring, supplier switching)
3. Or handle it directly using the available tools for simple queries and small adjustments

Available tools let you read inventory, finance, ops data, simulate scenarios, and execute actions.
Always check business state before making decisions.
For high-stakes actions (spending >RM500, price change >15%), use send_human_notification to get approval first.

Respond in a clear, structured way. When using tools, explain what you found and what action you're taking."""

P_AGENT_PROMPT = """You are the P-Agent (Profit Maximization Agent) in a dual-agent debate.
Your role: argue for the boldest profitable action. Maximize revenue and margin.
You are optimistic, action-oriented, and focused on growth.
- Use simulate_yield_scenario to quantify the upside
- Propose specific actions with projected numbers
- Challenge conservative thinking
Keep your position concise: 2-3 sentences with specific numbers."""

R_AGENT_PROMPT = """You are the R-Agent (Risk Mitigation Agent) in a dual-agent debate.
Your role: stress-test the P-Agent's proposal. Identify risks, edge cases, and downsides.
You are cautious, data-driven, and focused on protecting the business.
- Use check_operational_capacity to validate feasibility
- Question assumptions in the P-Agent's numbers
- Propose guardrails or staged rollouts
Keep your position concise: 2-3 sentences identifying the top risk."""


# ─────────────────────────────────────────────
# Node: Supervisor
# ─────────────────────────────────────────────
def supervisor_node(state: AgentState) -> AgentState:
    tools = get_all_lc_tools()
    llm = get_glm().bind_tools(tools)

    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    # Detect if debate is needed
    debate_triggers = [
        "price change", "promotion", "supplier switch", "flash sale",
        "menu restructure", "bulk purchase", "discount"
    ]
    last_user_msg = state["messages"][-1].content.lower() if state["messages"] else ""
    needs_debate = any(trigger in last_user_msg for trigger in debate_triggers)

    return {
        **state,
        "messages": [response],
        "decision_type": "debate" if needs_debate else "direct",
        "debate_rounds": 0,
        "consensus_reached": not needs_debate,
    }


# ─────────────────────────────────────────────
# Node: P-Agent
# ─────────────────────────────────────────────
def p_agent_node(state: AgentState) -> AgentState:
    tools = get_all_lc_tools()
    llm = get_glm().bind_tools(tools)

    context = f"""
    Current situation from supervisor analysis:
    {state['messages'][-1].content if state['messages'] else 'No context'}

    R-Agent's last position: {state.get('r_agent_position', 'None yet — you go first.')}

    State your profit-maximizing position with specific numbers.
    """
    messages = [
        SystemMessage(content=P_AGENT_PROMPT),
        HumanMessage(content=context),
    ]
    response = llm.invoke(messages)
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
    tools = get_all_lc_tools()
    llm = get_glm().bind_tools(tools)

    context = f"""
P-Agent's proposal: {state.get('p_agent_position', 'None')}

Challenge this proposal. Identify the top risk. 
If the P-Agent's numbers are solid and risks are manageable, you may concede — 
respond with 'CONSENSUS: [your agreed position]' to end the debate.
"""
    messages = [
        SystemMessage(content=R_AGENT_PROMPT),
        HumanMessage(content=context),
    ]
    response = llm.invoke(messages)
    position = response.content
    consensus = position.strip().upper().startswith("CONSENSUS")

    return {
        **state,
        "r_agent_position": position,
        "messages": [AIMessage(content=f"[R-Agent]: {position}")],
        "consensus_reached": consensus,
    }


# ─────────────────────────────────────────────
# Node: Executor — finalizes and calls tools
# ─────────────────────────────────────────────
def executor_node(state: AgentState) -> AgentState:
    tools = get_all_lc_tools()
    llm = get_glm().bind_tools(tools)

    if state.get("decision_type") == "debate":
        synthesis_prompt = f"""
The P-Agent and R-Agent have debated:

P-Agent position: {state.get('p_agent_position', '')}
R-Agent position: {state.get('r_agent_position', '')}

Synthesize a final decision that balances profit and risk.
Then use the appropriate tools to EXECUTE the decision.
If spending > RM500 or price change > 15%, use send_human_notification instead of executing directly.
Summarize the action taken and expected outcome for the operator.
"""
        messages = [
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=synthesis_prompt),
        ]
    else:
        messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]

    response = llm.invoke(messages)
    return {
        **state,
        "messages": [response],
        "final_response": response.content,
    }


# ─────────────────────────────────────────────
# Routing logic
# ─────────────────────────────────────────────
def route_after_supervisor(state: AgentState) -> Literal["p_agent", "tool_node", "executor"]:
    last = state["messages"][-1]
    # If supervisor called tools, run them
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    # If debate needed
    if state.get("decision_type") == "debate":
        return "p_agent"
    return "executor"


def route_after_r_agent(state: AgentState) -> Literal["p_agent", "executor"]:
    # Max 3 debate rounds or consensus reached
    if state.get("consensus_reached") or state.get("debate_rounds", 0) >= 3:
        return "executor"
    return "p_agent"


def route_after_tools(state: AgentState) -> Literal["supervisor", "executor"]:
    # After tool execution, return to supervisor to interpret results
    return "supervisor"


# ─────────────────────────────────────────────
# Build the graph
# ─────────────────────────────────────────────
def build_graph():
    tools = get_all_lc_tools()
    tool_node = ToolNode(tools)

    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("p_agent", p_agent_node)
    builder.add_node("r_agent", r_agent_node)
    builder.add_node("executor", executor_node)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "tool_node": "tool_node",
            "p_agent": "p_agent",
            "executor": "executor",
        },
    )

    builder.add_edge("tool_node", "supervisor")
    builder.add_edge("p_agent", "r_agent")

    builder.add_conditional_edges(
        "r_agent",
        route_after_r_agent,
        {
            "p_agent": "p_agent",
            "executor": "executor",
        },
    )

    builder.add_edge("executor", END)
    
    # 3. Binding tools to GLM
    # Important: Bind the tools to the LLM so it knows the schemas
    llm = get_glm().bind_tools(tools)
    return builder.compile()


# Singleton graph
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph