"""
proactive_graph.py — Proactive Crisis Response (fixed)

Fixes from original:
1. tool_node no longer routes to END — it routes back to whichever handler called it
   via a 'pending_handler' field in state (the diagram shows the loop continuing,
   not terminating after tool execution).
2. kitchen_surge_handler now includes execute_operational_action (rewrite menu) and
   generate_post_mortem_learning (log + post-mortem), both of which appear in the diagram.
3. stock_crisis_handler now includes contact_supplier for the CREATE_PO step shown
   in the 'Log + post-mortem' box at bottom of diagram.
4. Both handlers properly loop back through tool_node until no more tool calls are made,
   then route to END.
"""

from typing import Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools.mcp_tools_call import get_all_lc_tools
from app.core.glm_client import GLMClient

get_glm = lambda: GLMClient()


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class ProactiveState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    anomaly_type: Literal["stock_critical", "kitchen_surge", "none", "unknown"]
    # Tracks which handler is active so tool_node knows where to return
    pending_handler: Literal["stock_crisis_handler", "kitchen_surge_handler", "none"]
    action_taken: bool


# ─────────────────────────────────────────────
# Node 1: Anomaly classifier
# ─────────────────────────────────────────────
def anomaly_classifier_node(state: ProactiveState) -> ProactiveState:
    """
    Reads the DB alert message and classifies it.
    Strictly returns one classification word so routing is deterministic.
    """
    llm = get_glm()
    prompt = """You are the Proactive Monitor. Analyze the system alert.
Classify it strictly as one of:
- 'stock_critical'  → inventory level for any item is below safety threshold (qty < 1 day supply)
- 'kitchen_surge'   → active order queue is spiking OR kitchen_load_percent > 85%
- 'none'            → no actionable anomaly

Respond ONLY with the single classification word. No explanation."""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    classification = response.content.strip().lower()

    valid = {"stock_critical", "kitchen_surge", "none"}
    anomaly = classification if classification in valid else "unknown"

    return {**state, "anomaly_type": anomaly, "pending_handler": "none"}


# ─────────────────────────────────────────────
# Node 2a: Stock crisis handler
# ─────────────────────────────────────────────
def stock_crisis_handler(state: ProactiveState) -> ProactiveState:
    """
    Stock Critical path from diagram:
    simulate_yield_scenario → formulate_marketing_strategy (Flash Sale)
    → send_human_notification → execute_operational_action (CREATE_PO)
    → generate_post_mortem_learning
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "simulate_yield_scenario",
        "formulate_marketing_strategy",
        "send_human_notification",
        "execute_operational_action",
        "generate_post_mortem_learning",
        "contact_supplier",           # for CREATE_PO notification to supplier
        "get_business_state",         # to read current margin before simulating
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """STOCK CRITICAL ALERT. Execute the full stock crisis response in sequence:

Step 1 — Evaluate margin:
  Call get_business_state(scope='inventory') to identify the critical item.
  Call simulate_yield_scenario on the most affected menu item with action='discount', value=0.25
  to model the flash sale margin impact.

Step 2 — Launch flash sale:
  Call formulate_marketing_strategy with:
    strategy_type = 'FLASH_SALE'
    goal = 'clear_stock'
    config = { discount: 0.25, audience: 'all', budget: 50 }

Step 3 — Notify operator:
  Call send_human_notification with priority='high'. Include: item name, current qty,
  flash sale campaign_id, margin impact from simulation, and recommended PO.

Step 4 — Log the purchase order:
  Call execute_operational_action with action_type='CREATE_PO'.
  Call contact_supplier with message_type='emergency_restock' for the primary supplier.

Step 5 — Post-mortem:
  Call generate_post_mortem_learning to close the audit trail."""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    return {
        **state,
        "messages": [response],
        "pending_handler": "stock_crisis_handler",
        "action_taken": True,
    }


# ─────────────────────────────────────────────
# Node 2b: Kitchen surge handler
# ─────────────────────────────────────────────
def kitchen_surge_handler(state: ProactiveState) -> ProactiveState:
    """
    Kitchen Surge path from diagram:
    check_operational_capacity → get_all_menu_items (find substitutes)
    → execute_operational_action (UPDATE_MENU — rewrite to alt ingredient)
    → save_to_kds (Alert KDS + resequence with ETAs)
    → send_human_notification
    → generate_post_mortem_learning (Log + post-mortem)
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "check_operational_capacity",
        "get_all_menu_items",
        "execute_operational_action",   # UPDATE_MENU to switch ingredient
        "save_to_kds",                  # Alert KDS + resequence
        "send_human_notification",
        "generate_post_mortem_learning",
        "get_business_state",           # read current kitchen_load
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """KITCHEN SURGE DETECTED. Execute the full kitchen surge response in sequence:

Step 1 — Validate bottleneck:
  Call get_business_state(scope='ops') to get current kitchen_load_percent and pending_orders.
  Call check_operational_capacity with:
    projected_order_surge = pending_orders (from ops state)
    complexity_factor = 3 (assume medium complexity)

Step 2 — Find substitutes and rewrite menu:
  Call get_all_menu_items() to find fast-prep alternative dishes in the same category
  as the item causing the bottleneck.
  Call execute_operational_action with action_type='UPDATE_MENU' to temporarily
  mark slow items as unavailable and feature the fast-prep alternatives.

Step 3 — Alert KDS and resequence:
  Call save_to_kds for the updated menu instructions with:
    priority = 'urgent'
    agent_note = brief instruction to kitchen (e.g. 'Surge detected. Switch to noodle base.')
    estimated_prep_minutes = reduced estimate for the fast-prep alternatives

Step 4 — Notify operator:
  Call send_human_notification with priority='high'. Include: surge magnitude,
  menu changes made, KDS entry ID, recommended_staff_addition from capacity check.

Step 5 — Post-mortem:
  Call generate_post_mortem_learning to log this surge event."""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    return {
        **state,
        "messages": [response],
        "pending_handler": "kitchen_surge_handler",
        "action_taken": True,
    }


# ─────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────
def route_anomaly(state: ProactiveState) -> str:
    if state["anomaly_type"] == "stock_critical":
        return "stock_crisis_handler"
    if state["anomaly_type"] == "kitchen_surge":
        return "kitchen_surge_handler"
    return END


def route_tools(state: ProactiveState) -> str:
    """
    KEY FIX: After tool_node executes, route back to whichever handler
    is still active (pending_handler), not to END.
    This implements the tool-call loop shown in the diagram.
    """
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END


def route_after_tools(state: ProactiveState) -> str:
    """
    Routes tool_node output back to the correct handler.
    Without this, tool results are never interpreted — the handler that
    requested the tool never sees the response.
    """
    handler = state.get("pending_handler", "none")
    if handler == "stock_crisis_handler":
        return "stock_crisis_handler"
    if handler == "kitchen_surge_handler":
        return "kitchen_surge_handler"
    return END


# ─────────────────────────────────────────────
# Build graph
# ─────────────────────────────────────────────
def build_proactive_graph():
    builder = StateGraph(ProactiveState)

    builder.add_node("anomaly_classifier",    anomaly_classifier_node)
    builder.add_node("stock_crisis_handler",  stock_crisis_handler)
    builder.add_node("kitchen_surge_handler", kitchen_surge_handler)
    builder.add_node("tool_node",             ToolNode(get_all_lc_tools()))

    builder.add_edge(START, "anomaly_classifier")

    builder.add_conditional_edges("anomaly_classifier", route_anomaly, {
        "stock_crisis_handler":  "stock_crisis_handler",
        "kitchen_surge_handler": "kitchen_surge_handler",
        END:                     END,
    })

    # Both handlers: if they emit tool_calls → tool_node, else → END
    builder.add_conditional_edges("stock_crisis_handler",  route_tools, {
        "tool_node": "tool_node",
        END:         END,
    })
    builder.add_conditional_edges("kitchen_surge_handler", route_tools, {
        "tool_node": "tool_node",
        END:         END,
    })

    # KEY FIX: tool_node routes back to whoever called it
    builder.add_conditional_edges("tool_node", route_after_tools, {
        "stock_crisis_handler":  "stock_crisis_handler",
        "kitchen_surge_handler": "kitchen_surge_handler",
        END:                     END,
    })

    return builder.compile()


_proactive_graph = None

def get_proactive_graph():
    global _proactive_graph
    if _proactive_graph is None:
        _proactive_graph = build_proactive_graph()
    return _proactive_graph