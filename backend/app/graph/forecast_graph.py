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

    user_query: str

    signal_summary: str
    forecast_result: str

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

    return {
        **state,
        "messages": [response],
        "forecast_result": response.content,
        "node_tool_call_count": 0,
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
    return "signal_agent"


def route_after_signal(state: ForecastState):
    return "forecast_agent"


def route_after_forecast(state: ForecastState):
    return END


# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────

def build_forecast_graph():
    builder = StateGraph(ForecastState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("signal_agent", signal_agent_node)
    builder.add_node("forecast_agent", forecast_agent_node)
    builder.add_node("tool_node", ToolNode(get_all_lc_tools()))

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges("supervisor", route_after_supervisor, {
        "tool_node": "tool_node",
        "signal_agent": "signal_agent",
    })

    builder.add_edge("tool_node", "signal_agent")
    builder.add_edge("signal_agent", "forecast_agent")
    builder.add_edge("forecast_agent", END)

    return builder.compile()


_graph = None

def get_forecast_graph():
    global _graph
    if _graph is None:
        _graph = build_forecast_graph()
    return _graph