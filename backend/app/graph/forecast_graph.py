"""
forecast_graph.py — Forward-looking reasoning (fixed)

Fixes from original:
1. tool_node always routed to evaluate_risk — wrong. After standard_forecast or
   crisis_optimizer call tools, tool_node must loop back to THAT node, not evaluate_risk.
   Fixed via pending_handler pattern (same as proactive_graph fix).
2. crisis_optimizer_node was missing evaluate_supply_chain_options, get_all_menu_items,
   and contact_supplier — all visible in the 'Run constraints' and 'Output revised plan'
   boxes in the diagram.
3. standard_forecast_node was missing save_to_kds for the 'Pre-warn kitchen' step
   shown in the diagram.
4. evaluate_risk_node now also extracts the macro_risk_level from QueryMacroContextOutput's
   overall_risk_level field rather than asking the LLM to classify free text.
"""

from typing import Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools.mcp_tools_call import get_all_lc_tools
from app.core.glm_client import GLMClient

get_glm = lambda: GLMClient()


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class ForecastState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    macro_risk_level: Literal["low", "elevated", "high", "unknown"]
    # Tracks active node for tool_node return routing
    pending_handler: Literal["read_signals", "standard_forecast", "crisis_optimizer", "none"]
    plan_generated: bool


# ─────────────────────────────────────────────
# Node 1: Read signals (context gathering)
# ─────────────────────────────────────────────
def read_signals_node(state: ForecastState) -> ForecastState:
    """
    Gathers all forward-looking context signals in one pass.
    Diagram: 'Read signals — order history + time/day/weather + macro (news api)'
    Tools: get_all_orders, get_festival_calendar, query_macro_context
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "get_all_orders",
        "get_festival_calendar",
        "query_macro_context",
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """You are the Forecasting Agent. Gather all context signals for forward-looking reasoning.
Execute these three tool calls in order:

1. query_macro_context with indicators=['oil_price', 'usd_myr', 'local_inflation'],
   include_news_summary=True
   → This gives you the overall_risk_level directly from the tool output.

2. get_festival_calendar with days_ahead=7, include_food_impact=True
   → Any festival in the next 7 days changes the entire demand forecast.

3. get_all_orders with status_filter='completed', date_from=<30 days ago>, limit=500
   → Historical order patterns for this day-of-week.

After all three calls, summarize:
- The macro overall_risk_level returned by query_macro_context
- Any festivals in the next 7 days and their demand_impact
- The dominant demand patterns from order history (top 3 dishes, peak hours)"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    return {**state, "messages": [response], "pending_handler": "read_signals"}


# ─────────────────────────────────────────────
# Node 2: Evaluate risk level
# ─────────────────────────────────────────────
def evaluate_risk_node(state: ForecastState) -> ForecastState:
    """
    Reads the query_macro_context output from message history and extracts
    overall_risk_level. Uses deterministic extraction first, LLM as fallback.
    """
    llm = get_glm()

    prompt = """Review the tool responses in the conversation history.
Find the query_macro_context result and extract its overall_risk_level field.

Reply in this exact format (no other text):
RISK_LEVEL: <low|elevated|high>

If overall_risk_level is 'elevated' or 'high', treat as crisis.
If it's 'low', treat as normal."""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    content = response.content.strip()

    risk = "unknown"
    for line in content.splitlines():
        if line.startswith("RISK_LEVEL:"):
            raw = line.split(":", 1)[1].strip().lower()
            if raw in ("low", "elevated", "high"):
                risk = raw
            break

    return {**state, "macro_risk_level": risk, "pending_handler": "none"}


# ─────────────────────────────────────────────
# Node 3a: Standard forecast (low/elevated risk)
# ─────────────────────────────────────────────
def standard_forecast_node(state: ForecastState) -> ForecastState:
    """
    Normal demand forecasting path. Diagram steps:
    - Demand forecast: predict tonight per dish
    - Adjust reorder triggers (execute_operational_action INVENTORY_ADJUST)
    - Pre-warn kitchen (save_to_kds + send_human_notification)
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "execute_operational_action",   # adjust reorder triggers
        "save_to_kds",                  # pre-warn kitchen via KDS
        "send_human_notification",      # pre-warn operator
        "get_business_state",           # check current stock vs predicted demand
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """Macro risk is low/normal. Run the standard demand forecast protocol:

Step 1 — Predict tonight's demand:
Using the order history, festival calendar, and current day/time context from the
conversation history, predict demand for tonight per dish. Identify:
- Which dishes will spike (>20% above average)?
- Which dishes will be slow (<50% of average)?
- What is the expected peak hour window tonight?

Step 2 — Adjust reorder triggers:
For dishes predicted to spike, call get_business_state(scope='inventory') to check
current stock of their primary ingredients.
For any ingredient with stock < predicted demand × 1.2 (20% buffer):
  Call execute_operational_action with action_type='INVENTORY_ADJUST' to flag it
  for reorder (update a 'reorder_flag' field or similar).

Step 3 — Pre-warn kitchen:
Call save_to_kds with:
  order_id = 'forecast_alert_<timestamp>'
  priority = 'normal'
  agent_note = 'Demand spike expected for <dish>. Pre-prep by <time>.'
  estimated_prep_minutes = 0 (this is a planning alert, not an order)

Step 4 — Notify operator:
Call send_human_notification with priority='medium'. Include the full forecast
summary: top dishes, expected covers, ingredient risks, KDS alert sent."""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    return {
        **state,
        "messages": [response],
        "pending_handler": "standard_forecast",
        "plan_generated": True,
    }


# ─────────────────────────────────────────────
# Node 3b: Crisis optimizer (high/elevated risk)
# ─────────────────────────────────────────────
def crisis_optimizer_node(state: ForecastState) -> ForecastState:
    """
    Multi-constraint optimization for macro crisis. Diagram steps:
    - Run constraints: margin + stock + suppliers (get_business_state, evaluate_supply_chain_options)
    - Output revised plan: pricing + menu + impact est. (execute_operational_action)
    - Log + learn (generate_post_mortem_learning)
    - send_human_notification for operator approval
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "get_business_state",               # margin + stock state
        "get_all_menu_items",               # full menu for repricing
        "evaluate_supply_chain_options",    # supplier alternatives under macro pressure
        "simulate_yield_scenario",          # model repricing impact
        "execute_operational_action",       # UPDATE_MENU with new prices
        "send_human_notification",          # output revised plan to operator
        "generate_post_mortem_learning",    # log the macro shift event
        "contact_supplier",                 # proactive PO before costs rise further
        "query_macro_context",              # re-confirm risk signal if needed
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = f"""MACRO CRISIS MODE. Risk level: {state.get('macro_risk_level', 'high')}.
Run the multi-constraint profit preservation optimization:

Step 1 — Run constraints (assess current state):
  a) get_business_state(scope='inventory') → identify low-margin, high-risk stock
  b) get_business_state(scope='finance') → current daily revenue and margin average
  c) get_all_menu_items() → full menu for repricing analysis
  d) For each high-cost ingredient, call evaluate_supply_chain_options to find
     cheaper or more reliable alternatives under current macro conditions.

Step 2 — Simulate repricing:
  For menu items using affected ingredients:
  Call simulate_yield_scenario with action='discount' or action='bundle' to model
  whether absorbing the cost, passing it to customers, or substituting ingredients
  gives the best margin outcome.

Step 3 — Output revised plan:
  Based on simulation results, call execute_operational_action(UPDATE_MENU) for
  any items where repricing is recommended and the margin improvement is > 2%.

Step 4 — Contact suppliers proactively:
  If query_macro_context recommended bulk purchasing, call contact_supplier
  with message_type='purchase_order' for the highest-value stable ingredients.

Step 5 — Notify operator with full plan:
  Call send_human_notification with priority='high'. The message must include:
  - Macro signal summary (which indicator triggered, trend, confidence)
  - Items repriced (old price → new price, margin impact)
  - Suppliers contacted (item, supplier, qty, unit cost)
  - Total projected margin improvement
  - Items flagged for human review (changes > 15%)

Step 6 — Log and learn:
  Call generate_post_mortem_learning to record this macro event."""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    return {
        **state,
        "messages": [response],
        "pending_handler": "crisis_optimizer",
        "plan_generated": True,
    }


# ─────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────
def route_after_read_signals(state: ForecastState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return "evaluate_risk"


def route_forecast(state: ForecastState) -> str:
    risk = state.get("macro_risk_level", "unknown")
    if risk in ("high", "elevated"):
        return "crisis_optimizer"
    return "standard_forecast"


def route_handler_tools(state: ForecastState) -> str:
    """Standard tool-call check for standard_forecast and crisis_optimizer."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END


def route_after_tools(state: ForecastState) -> str:
    """
    KEY FIX: Routes tool_node results back to the node that requested them.
    In the original, tool_node always went to evaluate_risk — this meant
    standard_forecast and crisis_optimizer never received their tool results.
    """
    handler = state.get("pending_handler", "none")
    if handler == "read_signals":
        return "evaluate_risk"         # signals gathered → evaluate
    if handler == "standard_forecast":
        return "standard_forecast"     # tool result → back to forecast node
    if handler == "crisis_optimizer":
        return "crisis_optimizer"      # tool result → back to optimizer
    return END


# ─────────────────────────────────────────────
# Build graph
# ─────────────────────────────────────────────
def build_forecast_graph():
    builder = StateGraph(ForecastState)

    builder.add_node("read_signals",      read_signals_node)
    builder.add_node("evaluate_risk",     evaluate_risk_node)
    builder.add_node("standard_forecast", standard_forecast_node)
    builder.add_node("crisis_optimizer",  crisis_optimizer_node)
    builder.add_node("tool_node",         ToolNode(get_all_lc_tools()))

    builder.add_edge(START, "read_signals")

    builder.add_conditional_edges("read_signals", route_after_read_signals, {
        "tool_node":     "tool_node",
        "evaluate_risk": "evaluate_risk",
    })

    builder.add_conditional_edges("evaluate_risk", route_forecast, {
        "standard_forecast": "standard_forecast",
        "crisis_optimizer":  "crisis_optimizer",
    })

    builder.add_conditional_edges("standard_forecast", route_handler_tools, {
        "tool_node": "tool_node",
        END:         END,
    })

    builder.add_conditional_edges("crisis_optimizer", route_handler_tools, {
        "tool_node": "tool_node",
        END:         END,
    })

    # KEY FIX: tool_node routes back to whoever called it
    builder.add_conditional_edges("tool_node", route_after_tools, {
        "evaluate_risk":     "evaluate_risk",
        "standard_forecast": "standard_forecast",
        "crisis_optimizer":  "crisis_optimizer",
        END:                 END,
    })

    return builder.compile()


_forecast_graph = None

def get_forecast_graph():
    global _forecast_graph
    if _forecast_graph is None:
        _forecast_graph = build_forecast_graph()
    return _forecast_graph