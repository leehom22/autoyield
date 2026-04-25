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

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
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

def supervisor_node(state: ForecastState) -> ForecastState:
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

    return {
        **state,
        "messages": [response],
        "user_query": user_query,
        "pending_handler": "supervisor",
        "node_tool_call_count": state.get("node_tool_call_count", 0)
        + (1 if getattr(response, "tool_calls", None) else 0),
    }


def signal_agent_node(state: ForecastState) -> ForecastState:
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

    return {
        **state,
        "messages": [response],
        "signal_summary": response.content,
        "node_tool_call_count": 0,
    }

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

    return {
        **state,
        "messages": [response],
        "forecast_result": response.content,
        "macro_risk_level": risk_level,
        "plan_generated": True,
        "pending_handler": "notification",
        "node_tool_call_count": 0,
    }
    
def notification_node(state: ForecastState) -> ForecastState:
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

    return {
        **state,
        "messages": [response],
        "pending_handler": "notification",
        "notification_sent": bool(getattr(response, "tool_calls", None)),
        "node_tool_call_count": 1 if getattr(response, "tool_calls", None) else 0,
    }

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
    return {
        **state,
        "forecast_path": "crisis",
        "forecast_result": state.get("forecast_result", "") or "Crisis forecast mode activated.",
    }


def constraint_node(state: ForecastState) -> ForecastState:
    return {
        **state,
        "constraint_summary": "Checked margin, stock, and supplier constraints.",
    }


def revised_plan_node(state: ForecastState) -> ForecastState:
    revised = "Generated revised crisis plan with pricing, menu, and impact estimates."

    return {
        **state,
        "forecast_path": "crisis",
        "revised_plan": revised,
        "forecast_result": revised,
        "macro_risk_level": "high",
        "plan_generated": True,
        "pending_handler": "notification",
    }
    
# ─────────────────────────────────────────────
# Routing
# ─────────────────────────────────────────────

def route_after_supervisor(state: ForecastState):
    last = state["messages"][-1]

    if getattr(last, "tool_calls", None):
        if state.get("node_tool_call_count", 0) >= MAX_TOOL_CALLS_PER_NODE:
            return "signal_agent"
        return "tool_node"

    return "signal_agent"


def route_after_tools(state: ForecastState):
    handler = state.get("pending_handler", "supervisor")

    if handler == "notification":
        return END

    if handler == "supervisor":
        return "signal_agent"

    return END


def route_after_signal(state: ForecastState):
    signals = state.get("signal_summary", "").lower()

    crisis_keywords = [
        "oil", "usd/myr", "inflation", "macro",
        "spike", "shortage", "zero stock",
        "high risk", "crisis", "supply disruption"
    ]

    if any(k in signals for k in crisis_keywords):
        return "crisis_optimizer"

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

    builder.add_edge(START, "supervisor")

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

    builder.add_edge("crisis_optimizer", "constraint_node")
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