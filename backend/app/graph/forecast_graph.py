import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools.mcp_tools_call import get_all_lc_tools

load_dotenv()

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
MAX_TOOL_CALLS_PER_NODE = 4
MAX_FORECAST_DEBATE_ROUNDS = 3

# ─────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────
def get_glm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("GLM_MODEL", "glm-4-plus"),
        api_key=os.getenv("GLM_API_KEY"),
        base_url=os.getenv("GLM_BASE_URL"),
        temperature=0.3,
    )


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class ForecastState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    forecast_path: str          # "standard" | "crisis"
    reorder_plan: str
    kitchen_warning: str
    constraint_summary: str
    revised_plan: str

    user_query: str
    signal_summary: str
    forecast_result: str

    macro_risk_level: str
    plan_generated: bool

    pending_handler: str
    notification_sent: bool
    notification_id: str

    node_tool_call_count: int
    
    p_agent_position: str
    r_agent_position: str
    debate_rounds: int
    consensus_reached: bool
    debate_started: bool


# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────
SUPERVISOR_PROMPT = """
You are the Forecast Supervisor.

STEP 1 — Identify if this is a demand forecasting request.

STEP 2 — ALWAYS fetch demand signals using tools:

1. get_festival_calendar(days_ahead=7)
2. get_business_state(scope='inventory')
3. get_business_state(scope='ops')

IMPORTANT:
- Do NOT call pricing tools
- Do NOT call supplier tools
- Do NOT simulate revenue
- Do NOT debate

After tools are done, output:
SIGNAL_READY: true
"""

SIGNAL_AGENT_PROMPT = """
You are a Demand Signal Extractor.

Convert raw tool outputs into structured demand signals.

Focus on:
- Festival demand changes
- Inventory constraints
- Operational capacity risks

Output ONLY bullet points.

Example:
- Chinese New Year in 3 days → +50% noodle demand
- Kitchen load already high → capacity risk
- Seafood low stock → constraint

Do NOT recommend actions.
"""

FORECAST_AGENT_PROMPT = """
You are the Demand Forecasting Agent.

Using the signals, predict:

1. Demand change (%)
2. Which items/categories will surge
3. Operational risk level (low/medium/high)

Output format:

Demand Forecast:
- %

Key Drivers:
- bullet points

Risk Level:
- low / medium / high

Recommendation:
- 1 short actionable suggestion

Do NOT call tools.
Do NOT debate.
"""

NOTIFICATION_PROMPT = """
You are the Forecast Notification Agent.

The forecast is finalized. Save it to the notifications table by calling send_human_notification exactly once.

Use ONLY send_human_notification.

Rules:
- priority = 'high' if risk level is high
- priority = 'medium' otherwise
- proposed_action_json must include:
  - type: forecast_plan
  - user_query
  - signal_summary
  - forecast_result
  - risk_level

Do not call any other tool.
"""

FORECAST_P_AGENT_PROMPT = """
    You are the Forecast P-Agent.

    Your job is to argue for the most business-beneficial macro-crisis response.

    Focus on:
    - protecting revenue
    - adjusting prices or menus
    - reducing waste
    - maintaining service continuity
    - using demand forecast signals

    Do NOT call tools.
    Give 2-4 sentences.
    End with one concrete recommendation.
"""

FORECAST_R_AGENT_PROMPT = """
    You are the Forecast R-Agent.

    Your job is to challenge the P-Agent's crisis response.

    Focus on:
    - operational risk
    - customer backlash
    - supply uncertainty
    - forecast uncertainty
    - execution risk

    If the P-Agent's proposal is acceptable, start with:
    CONSENSUS:

    Otherwise, state the biggest risk and one required guardrail.

    Do NOT call tools.
    Give 2-4 sentences.
"""
# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

DEBUG_GRAPH = True

RESET  = "\033[0m"
BOLD   = "\033[1m"
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
GRAY   = "\033[90m"


def subheader(text):
    if DEBUG_GRAPH:
        print(f"\n{BOLD}{BLUE} ▶ {text}{RESET}")


def ok(text):
    if DEBUG_GRAPH:
        print(f" {GREEN}✓ {text}{RESET}")


def warn(text):
    if DEBUG_GRAPH:
        print(f" {YELLOW}⚠ {text}{RESET}")


def dim(text):
    if DEBUG_GRAPH:
        print(f" {GRAY}{text}{RESET}")


def debug_state(node, state):
    if not DEBUG_GRAPH:
        return

    subheader(f"Node: {node}")

    fields = {
        "forecast_path": state.get("forecast_path"),
        "pending_handler": state.get("pending_handler"),
        "macro_risk_level": state.get("macro_risk_level"),
        "debate_rounds": state.get("debate_rounds"),
        "consensus_reached": state.get("consensus_reached"),
        "node_tool_call_count": state.get("node_tool_call_count"),
    }

    dim(f"State: {fields}")

    if state.get("messages"):
        last = state["messages"][-1]

        if getattr(last, "tool_calls", None):
            for tc in last.tool_calls:
                dim(
                    f"Tool call → "
                    f"{tc.get('name')}("
                    f"{str(tc.get('args',{}))[:150]})"
                )
        else:
            dim(
                f"Last message: "
                f"{type(last).__name__}: "
                f"{str(getattr(last,'content',''))[:250]}"
            )
            
def _safe_llm_call(llm, messages, node_name: str):
    try:
        return llm.invoke(messages)
    except Exception as e:
        return AIMessage(content=f"SYSTEM ERROR in {node_name}: {str(e)}")


def _extract_tool_summary(messages, max_results=3):
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    recent = tool_msgs[-max_results:]

    if not recent:
        return "No tool data."

    parts = []
    for tm in recent:
        content = str(tm.content)
        if len(content) > 400:
            content = content[:400] + "... [truncated]"
        parts.append(f"[{tm.name}]: {content}")

    return "\n".join(parts)


# ─────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────

def forecast_p_agent_node(state: ForecastState) -> ForecastState:
    llm = get_glm()

    context = (
        f"MACRO CRISIS REQUEST:\n{state.get('user_query', '')}\n\n"
        f"SIGNAL SUMMARY:\n{state.get('signal_summary', '')}\n\n"
        f"CURRENT FORECAST RESULT:\n{state.get('forecast_result', '')}\n\n"
        f"CONSTRAINT SUMMARY:\n{state.get('constraint_summary', '')}\n\n"
        "Propose the most profitable and practical crisis response."
    )

    response = _safe_llm_call(
        llm,
        [
            SystemMessage(content=FORECAST_P_AGENT_PROMPT),
            HumanMessage(content=context),
        ],
        "forecast_p_agent",
    )

    new_state = {
        **state,
        "messages": [response],
        "p_agent_position": response.content,
        "debate_started": True,
        "debate_rounds": state.get("debate_rounds", 0) + 1,
    }
    debug_state("forecast_p_agent:end", new_state)
    return new_state


def forecast_r_agent_node(state: ForecastState) -> ForecastState:
    llm = get_glm()

    context = (
        f"MACRO CRISIS REQUEST:\n{state.get('user_query', '')}\n\n"
        f"SIGNAL SUMMARY:\n{state.get('signal_summary', '')}\n\n"
        f"P-AGENT PROPOSAL:\n{state.get('p_agent_position', '')}\n\n"
        "Critique the proposal and decide whether to accept it."
    )

    response = _safe_llm_call(
        llm,
        [
            SystemMessage(content=FORECAST_R_AGENT_PROMPT),
            HumanMessage(content=context),
        ],
        "forecast_r_agent",
    )

    content = response.content
    consensus = content.strip().upper().startswith("CONSENSUS")

    new_state = {
        **state,
        "messages": [AIMessage(content=f"[Forecast R-Agent]: {content}")],
        "r_agent_position": content,
        "consensus_reached": consensus,
    }
    debug_state("forecast_r_agent:end", new_state)
    return new_state
    
def supervisor_node(state: ForecastState) -> ForecastState:
    debug_state("supervisor:start", state)
    llm = get_glm().bind_tools(get_all_lc_tools())

    user_query = state.get("user_query", "")
    if not user_query:
        for m in reversed(state["messages"]):
            if isinstance(m, HumanMessage):
                user_query = m.content
                break

    response = _safe_llm_call(
        llm,
        [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"],
        "supervisor"
    )

    new_state = {
        **state,
        "messages": [response],
        "user_query": user_query,
        "pending_handler": "supervisor",
        "node_tool_call_count": state.get("node_tool_call_count", 0)
        + (1 if getattr(response, "tool_calls", None) else 0),
    }
    debug_state("supervisor:start", new_state)
    return new_state


def signal_agent_node(state: ForecastState) -> ForecastState:
    debug_state("signal_agent:start", state)
    llm = get_glm()

    tool_summary = _extract_tool_summary(state["messages"])

    response = _safe_llm_call(
        llm,
        [
            SystemMessage(content=SIGNAL_AGENT_PROMPT),
            HumanMessage(content=tool_summary),
        ],
        "signal_agent"
    )

    new_state = {
        **state,
        "messages": [response],
        "signal_summary": response.content,
        "node_tool_call_count": 0,
    }
    debug_state("signal_agent:end", new_state)

def _extract_risk_level(text: str) -> str:
    lower = text.lower()
    if "risk level:" in lower:
        risk_block = lower.split("risk level:", 1)[1][:100]
        if "high" in risk_block:
            return "high"
        if "medium" in risk_block:
            return "elevated"
        if "low" in risk_block:
            return "low"
    return "unknown"

def forecast_agent_node(state: ForecastState) -> ForecastState:
    debug_state("forecast_agent:start", state)
    llm = get_glm()

    context = (
        f"USER REQUEST:\n{state.get('user_query')}\n\n"
        f"SIGNALS:\n{state.get('signal_summary')}\n\n"
        "Generate demand forecast."
    )

    response = _safe_llm_call(
        llm,
        [
            SystemMessage(content=FORECAST_AGENT_PROMPT),
            HumanMessage(content=context),
        ],
        "forecast_agent"
    )

    risk_level = _extract_risk_level(response.content)

    new_state = {
        **state,
        "messages": [response],
        "forecast_result": response.content,
        "macro_risk_level": risk_level,
        "plan_generated": True,
        "pending_handler": "notification",
        "node_tool_call_count": 0,
    }
    debug_state("forecast_agent:start", new_state)
    return new_state
    
def notification_node(state: ForecastState) -> ForecastState:
    debug_state("forecast_agent:start", state)
    if state.get("notification_sent", False):
        return {
            **state,
            "pending_handler": "none",
            "node_tool_call_count": 0,
        }

    tools = [
        t for t in get_all_lc_tools()
        if t.name == "send_human_notification"
    ]

    llm = get_glm().bind_tools(tools)

    risk_level = state.get("macro_risk_level", "unknown")
    priority = "high" if risk_level == "high" else "medium"

    context = (
        f"RISK LEVEL: {risk_level}\n"
        f"PRIORITY: {priority}\n\n"
        f"USER QUERY:\n{state.get('user_query', '')}\n\n"
        f"SIGNAL SUMMARY:\n{state.get('signal_summary', '')}\n\n"
        f"FORECAST RESULT:\n{state.get('forecast_result', '')}\n\n"
        "Call send_human_notification exactly once."
    )

    response = _safe_llm_call(
        llm,
        [
            SystemMessage(content=NOTIFICATION_PROMPT),
            HumanMessage(content=context),
        ],
        "notification_node"
    )

    new_state = {
        **state,
        "messages": [response],
        "pending_handler": "notification",
        "notification_sent": bool(getattr(response, "tool_calls", None)),
        "node_tool_call_count": 1 if getattr(response, "tool_calls", None) else 0,
    }
    debug_state("forecast_agent:end", new_state)
    return new_state
    

def reorder_trigger_node(state: ForecastState) -> ForecastState:
    return {
        **state,
        "reorder_plan": "Adjust reorder triggers based on forecasted demand and inventory risk.",
    }


def kitchen_prewarn_node(state: ForecastState) -> ForecastState:
    return {
        **state,
        "kitchen_warning": "Pre-warn kitchen about forecasted demand and capacity constraints.",
    }


def crisis_optimizer_node(state: ForecastState) -> ForecastState:
    crisis_msg = state.get("user_query", "") or state.get("signal_summary", "")

    
    new_state = {
        **state,
        "forecast_path": "crisis",
        "signal_summary": state.get("signal_summary", "") or crisis_msg,
        "forecast_result": (
            state.get("forecast_result", "")
            or f"Macro crisis optimizer activated: {crisis_msg}"
        ),
        "macro_risk_level": "high",
        "debate_started": False,
        "p_agent_position": "",
        "r_agent_position": "",
        "debate_rounds": 0,
        "consensus_reached": False,
        "pending_handler": "crisis_optimizer",
        "node_tool_call_count": 0,
    }
    debug_state("crisis_optimizer:end", new_state)
    return new_state

def constraint_node(state: ForecastState) -> ForecastState:
    return {
        **state,
        "constraint_summary": "Checked margin, stock, and supplier constraints.",
    }


def revised_plan_node(state: ForecastState) -> ForecastState:
    revised = (
        "Generated revised macro-crisis plan based on P/R debate.\n\n"
        f"P-Agent Position:\n{state.get('p_agent_position', '')}\n\n"
        f"R-Agent Position:\n{state.get('r_agent_position', '')}\n\n"
        "Final Plan: Apply the agreed crisis response with high-priority monitoring."
    )

    new_state = {
        **state,
        "forecast_path": "crisis",
        "revised_plan": revised,
        "forecast_result": revised,
        "macro_risk_level": "high",
        "plan_generated": True,
        "pending_handler": "notification",
    }
    debug_state("revised_plan:end", new_state)
    return new_state
    
# ─────────────────────────────────────────────
# Routing
# ─────────────────────────────────────────────

def route_from_start(state):
    debug_state("route_from_start", state)

    if state.get("forecast_path") == "crisis":
        ok("START → crisis_optimizer")
        return "crisis_optimizer"

    ok("START → supervisor")
    return "supervisor"

def route_after_supervisor(state):
    debug_state("route_after_supervisor", state)

    last = state["messages"][-1]

    if getattr(last,"tool_calls",None):

        if state.get("node_tool_call_count",0)>=MAX_TOOL_CALLS_PER_NODE:
            warn("Supervisor tool cap reached → signal_agent")
            return "signal_agent"

        ok("supervisor → tool_node")
        return "tool_node"

    ok("supervisor → signal_agent")
    return "signal_agent"


def route_after_forecast_r_agent(state):
    debug_state("route_after_forecast_r_agent", state)

    if state.get("consensus_reached"):
        ok("Debate consensus → constraint_node")
        return "constraint_node"

    if state.get("debate_rounds",0)>=MAX_FORECAST_DEBATE_ROUNDS:
        warn("Max debate rounds hit → constraint_node")
        return "constraint_node"

    ok("Looping debate → forecast_p_agent")
    return "forecast_p_agent"

def route_after_tools(state):
    debug_state("route_after_tools", state)

    handler=state.get("pending_handler","supervisor")

    if handler=="notification":
        ok("tool_node → END")
        return END

    if handler=="supervisor":
        ok("tool_node → signal_agent")
        return "signal_agent"

    warn("tool_node fallback → END")
    return END


def route_after_signal(state):
    debug_state("route_after_signal", state)

    signals=state.get("signal_summary","").lower()

    crisis_keywords=[
        "oil","usd/myr","inflation",
        "spike","shortage","crisis"
    ]

    if any(k in signals for k in crisis_keywords):
        ok("signal_agent → crisis_optimizer")
        return "crisis_optimizer"

    ok("signal_agent → standard_forecast")
    return "standard_forecast"


def route_after_forecast(state: ForecastState):
    if state.get("plan_generated", False):
        return "notification_node"
    return END

def route_after_notification(state: ForecastState):
    last = state["messages"][-1]

    if getattr(last, "tool_calls", None):
        return "tool_node"

    return END

# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────

def build_forecast_graph():
    builder = StateGraph(ForecastState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("tool_node", ToolNode(get_all_lc_tools()))
    builder.add_node("signal_agent", signal_agent_node)

    builder.add_node("standard_forecast", forecast_agent_node)
    builder.add_node("reorder_trigger", reorder_trigger_node)
    builder.add_node("kitchen_prewarn", kitchen_prewarn_node)

    builder.add_node("crisis_optimizer", crisis_optimizer_node)
    builder.add_node("constraint_node", constraint_node)
    builder.add_node("revised_plan", revised_plan_node)

    builder.add_node("notification_node", notification_node)

    builder.add_node("forecast_p_agent", forecast_p_agent_node)
    builder.add_node("forecast_r_agent", forecast_r_agent_node)

    builder.add_conditional_edges(START, route_from_start, {
        "supervisor": "supervisor",
        "crisis_optimizer": "crisis_optimizer",
    })
    
    builder.add_conditional_edges("supervisor", route_after_supervisor, {
        "tool_node": "tool_node",
        "signal_agent": "signal_agent",
    })

    builder.add_conditional_edges("tool_node", route_after_tools, {
        "signal_agent": "signal_agent",
        END: END,
    })

    builder.add_conditional_edges("signal_agent", route_after_signal, {
        "standard_forecast": "standard_forecast",
        "crisis_optimizer": "crisis_optimizer",
    })

    builder.add_edge("standard_forecast", "reorder_trigger")
    builder.add_edge("reorder_trigger", "kitchen_prewarn")
    builder.add_edge("kitchen_prewarn", "notification_node")

    builder.add_edge("crisis_optimizer", "forecast_p_agent")
    builder.add_edge("forecast_p_agent", "forecast_r_agent")
    builder.add_conditional_edges("forecast_r_agent", route_after_forecast_r_agent, {
        "forecast_p_agent": "forecast_p_agent",
        "constraint_node": "constraint_node",
    })
    builder.add_edge("constraint_node", "revised_plan")
    builder.add_edge("revised_plan", "notification_node")

    builder.add_conditional_edges("notification_node", route_after_notification, {
        "tool_node": "tool_node",
        END: END,
    })

    return builder.compile()


_graph = None

def get_forecast_graph():
    global _graph
    if _graph is None:
        _graph = build_forecast_graph()
    return _graph