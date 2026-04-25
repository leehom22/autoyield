"""
proactive_graph.py — Proactive Crisis Response (fixed)
"""

from typing import Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools.mcp_tools_call import get_all_lc_tools
from langchain_openai import ChatOpenAI
import os

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
class ProactiveState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    anomaly_type: Literal["stock_critical", "kitchen_surge", "none", "unknown"]
    pending_handler: str

    margin_summary: str
    capacity_summary: str
    menu_rewrite_summary: str
    kds_summary: str
    final_response: str

    action_taken: bool
    node_tool_call_count: int

    direct_route: str
    crisis_message: str
    crisis_summary: str

# ─────────────────────────────────────────────
# Node 1: Anomaly classifier
# ─────────────────────────────────────────────
import os

DEBUG_GRAPH = os.getenv("DEBUG_GRAPH", "true").lower() == "true"

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
        "anomaly_type": state.get("anomaly_type"),
        "pending_handler": state.get("pending_handler"),
        "action_taken": state.get("action_taken"),
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
                    f"{str(tc.get('args', {}))[:120]})"
                )
        else:
            dim(
                f"Last message: "
                f"{type(last).__name__}: "
                f"{str(getattr(last,'content',''))[:250]}"
            )
            
            
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
    has_tool = bool(getattr(response, "tool_calls", None))

    new_state = {
        **state,
        "anomaly_type": anomaly,
    }

    debug_state("anomaly_classifier:end", new_state)
    return new_state



# ──────────────────────────────────────────────
# Tool-handling nodes
# ──────────────────────────────────────────────


def evaluate_margin_node(state: ProactiveState) -> ProactiveState:
    tools = [t for t in get_all_lc_tools() if t.name in [
        "get_business_state",
        "simulate_yield_scenario",
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """
STOCK CRITICAL: Evaluate margin impact.
Call get_business_state(scope='inventory').
Then call simulate_yield_scenario only if you can identify the affected menu item.
Summarize the margin impact.
"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    has_tool = bool(getattr(response, "tool_calls", None))

    new_state ={
        **state,
        "messages": [response],
        "pending_handler": "evaluate_margin",
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if has_tool else 0),

    }

    debug_state("evaluate_margin:end", new_state)
    return new_state


def flash_sale_node(state: ProactiveState) -> ProactiveState:
    tools = [t for t in get_all_lc_tools() if t.name == "formulate_marketing_strategy"]
    llm = get_glm().bind_tools(tools)

    prompt = """
Launch a controlled FLASH_SALE to clear critical stock.
Call formulate_marketing_strategy with:
strategy_type='FLASH_SALE'
goal='clear_stock'
config={discount:0.25, audience:'all', budget:50}
"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    has_tool = bool(getattr(response, "tool_calls", None))
    
    new_state = {
        **state,
        "messages": [response],
        "pending_handler": "flash_sale",
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if has_tool else 0),
    }
    
    debug_state("flash_sale:end", new_state)
    return new_state


def notify_frontend_log_node(state: ProactiveState) -> ProactiveState:
    tools = [t for t in get_all_lc_tools() if t.name in [
        "send_human_notification",
        "execute_operational_action",
        "contact_supplier",
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """
Before calling contact_supplier, only use supplier_id if it is a valid UUID from tool results.
Do NOT invent supplier IDs like SUP-001.
If no UUID is known:
use send_human_notification instead and ask the operator to confirm the supplier.
If got a valid UUID:
Notify operator and log operational action.
Use send_human_notification(priority='high').
If restock is needed, call execute_operational_action(action_type='CREATE_PO').
If supplier contact is needed, call contact_supplier(message_type='emergency_restock').
"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    has_tool = bool(getattr(response, "tool_calls", None))

    new_state = {
        **state,
        "messages": [response],
        "pending_handler": "notify_frontend_log",
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if has_tool else 0),
        "action_taken": True,
    }
    debug_state("notify_frontend_log:end", new_state)
    return new_state


def check_capacity_node(state: ProactiveState) -> ProactiveState:
    tools = [t for t in get_all_lc_tools() if t.name in [
        "get_business_state",
        "check_operational_capacity",
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """
KITCHEN SURGE: Validate bottleneck.
Call get_business_state(scope='ops').
Then call check_operational_capacity using pending_orders as projected_order_surge and complexity_factor=3.
"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    has_tool = bool(getattr(response, "tool_calls", None))

    new_state = {
        **state,
        "messages": [response],
        "pending_handler": "check_capacity",
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if has_tool else 0),
    }
    debug_state("check_capacity:end", new_state)
    return new_state

def rewrite_menu_node(state: ProactiveState) -> ProactiveState:
    tools = [t for t in get_all_lc_tools() if t.name in [
        "get_all_menu_items",
        "execute_operational_action",
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """
Rewrite menu for kitchen surge.
Call get_all_menu_items to find faster-prep alternatives.
Then call execute_operational_action(action_type='UPDATE_MENU') to temporarily feature fast-prep alternatives or hide slow items.
"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    has_tool = bool(getattr(response, "tool_calls", None))

    
    new_state =  {
        **state,
        "messages": [response],
        "pending_handler": "rewrite_menu",
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if has_tool else 0),
    }
    debug_state("rewrite_menu:end", new_state)
    return new_state


def alert_kds_node(state: ProactiveState) -> ProactiveState:
    tools = [t for t in get_all_lc_tools() if t.name in [
        "save_to_kds",
        "send_human_notification",
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """
Alert KDS and notify operator.
Call save_to_kds with priority='urgent'.
Then call send_human_notification(priority='high') summarizing surge, menu changes, and KDS action.
"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    has_tool = bool(getattr(response, "tool_calls", None))

    new_state = {
        **state,
        "messages": [response],
        "pending_handler": "alert_kds",
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if has_tool else 0),
        "action_taken": True,
    }
    debug_state("alert_kds:end", new_state)
    return new_state


def postmortem_node(state: ProactiveState) -> ProactiveState:
    tools = [t for t in get_all_lc_tools() if t.name == "generate_post_mortem_learning"]
    llm = get_glm().bind_tools(tools)

    prompt = """
Close the audit trail.
Call generate_post_mortem_learning for this proactive event.
"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    has_tool = bool(getattr(response, "tool_calls", None))

    new_state = {
        **state,
        "messages": [response],
        "pending_handler": "postmortem",
        "node_tool_call_count": state.get("node_tool_call_count", 0) + (1 if has_tool else 0),
        "final_response": "Proactive response completed and logged.",
    }
    debug_state("postmortem:end", new_state)
    return new_state

def crisis_optimizer_node(state: ProactiveState) -> ProactiveState:
    crisis_msg = state.get("crisis_message", "")

    lower = crisis_msg.lower()

    if "inventory" in lower or "stock" in lower or "below minimum" in lower:
        anomaly_type = "stock_critical"
        summary = f"Crisis optimizer routed to stock-critical flow: {crisis_msg}"

    elif "order" in lower or "surge" in lower or "kitchen" in lower:
        anomaly_type = "kitchen_surge"
        summary = f"Crisis optimizer routed to kitchen-surge flow: {crisis_msg}"

    else:
        anomaly_type = "unknown"
        summary = f"Crisis optimizer could not classify crisis: {crisis_msg}"

    new_state = {
        **state,
        "anomaly_type": anomaly_type,
        "crisis_summary": summary,
        "pending_handler": "crisis_optimizer",
        "node_tool_call_count": 0,
    }

    debug_state("crisis_optimizer:end", new_state)
    return new_state

# ─────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────
def route_from_start(state: ProactiveState) -> str:
    debug_state("route_from_start", state)

    if state.get("direct_route") == "crisis_optimizer":
        ok("START → crisis_optimizer")
        return "crisis_optimizer"

    ok("START → anomaly_classifier")
    return "anomaly_classifier"

def route_after_crisis_optimizer(state: ProactiveState) -> str:
    debug_state("route_after_crisis_optimizer", state)

    if state.get("anomaly_type") == "stock_critical":
        ok("crisis_optimizer → evaluate_margin")
        return "evaluate_margin"

    if state.get("anomaly_type") == "kitchen_surge":
        ok("crisis_optimizer → check_capacity")
        return "check_capacity"

    warn("crisis_optimizer → END")
    return END

def route_anomaly(state):
    debug_state("route_anomaly", state)

    if state.get("anomaly_type")=="stock_critical":
        ok("Routing → evaluate_margin")
        return "evaluate_margin"

    if state.get("anomaly_type")=="kitchen_surge":
        ok("Routing → check_capacity")
        return "check_capacity"

    warn("Routing → END")
    return END

MAX_TOOL_CALLS_PER_NODE = 4

def route_tools(state):
    debug_state("route_tools", state)

    last = state["messages"][-1]
    has_tool_calls = bool(getattr(last, "tool_calls", None))
    tool_count = state.get("node_tool_call_count", 0)

    if has_tool_calls:
        if tool_count >= MAX_TOOL_CALLS_PER_NODE:
            warn("tool cap reached → next")
            return "__next__"

        ok("Routing → tool_node")
        return "tool_node"

    ok("Routing → next")
    return "__next__"


def route_after_tools(state: ProactiveState) -> str:
    debug_state("route_after_tools", state)

    handler = state.get("pending_handler", "none")

    if handler == "evaluate_margin":
        ok("tool_node → flash_sale")
        return "flash_sale"

    if handler == "flash_sale":
        ok("tool_node → notify_frontend_log")
        return "notify_frontend_log"

    if handler == "notify_frontend_log":
        ok("tool_node → postmortem")
        return "postmortem"

    if handler == "check_capacity":
        ok("tool_node → rewrite_menu")
        return "rewrite_menu"

    if handler == "rewrite_menu":
        ok("tool_node → alert_kds")
        return "alert_kds"

    if handler == "alert_kds":
        ok("tool_node → postmortem")
        return "postmortem"

    if handler == "postmortem":
        ok("tool_node → END")
        return END

    warn("tool_node → END | unknown handler")
    return END

# ─────────────────────────────────────────────
# Build graph
# ─────────────────────────────────────────────
def build_proactive_graph():
    builder = StateGraph(ProactiveState)

    builder.add_node("anomaly_classifier", anomaly_classifier_node)
    builder.add_node("crisis_optimizer", crisis_optimizer_node)
    
    builder.add_node("evaluate_margin", evaluate_margin_node)
    builder.add_node("flash_sale", flash_sale_node)
    builder.add_node("notify_frontend_log", notify_frontend_log_node)

    builder.add_node("check_capacity", check_capacity_node)
    builder.add_node("rewrite_menu", rewrite_menu_node)
    builder.add_node("alert_kds", alert_kds_node)

    builder.add_node("postmortem", postmortem_node)
    builder.add_node("tool_node", ToolNode(get_all_lc_tools()))

    builder.add_conditional_edges(START, route_from_start, {
        "anomaly_classifier": "anomaly_classifier",
        "crisis_optimizer": "crisis_optimizer",
    })
    
    builder.add_conditional_edges("crisis_optimizer", route_after_crisis_optimizer, {
        "evaluate_margin": "evaluate_margin",
        "check_capacity": "check_capacity",
        END: END,
    })
        
    
    builder.add_conditional_edges("anomaly_classifier", route_anomaly, {
        "evaluate_margin": "evaluate_margin",
        "check_capacity": "check_capacity",
        END: END,
    })

    builder.add_conditional_edges("evaluate_margin", route_tools, {
        "tool_node": "tool_node",
        "__next__": "flash_sale",
    })

    builder.add_conditional_edges("flash_sale", route_tools, {
        "tool_node": "tool_node",
        "__next__": "notify_frontend_log",
    })

    builder.add_conditional_edges("notify_frontend_log", route_tools, {
        "tool_node": "tool_node",
        "__next__": "postmortem",
    })

    builder.add_conditional_edges("check_capacity", route_tools, {
        "tool_node": "tool_node",
        "__next__": "rewrite_menu",
    })

    builder.add_conditional_edges("rewrite_menu", route_tools, {
        "tool_node": "tool_node",
        "__next__": "alert_kds",
    })

    builder.add_conditional_edges("alert_kds", route_tools, {
        "tool_node": "tool_node",
        "__next__": "postmortem",
    })

    builder.add_conditional_edges("postmortem", route_tools, {
        "tool_node": "tool_node",
        "__next__": END,
    })

    builder.add_conditional_edges("tool_node", route_after_tools, {
        "flash_sale": "flash_sale",
        "notify_frontend_log": "notify_frontend_log",
        "postmortem": "postmortem",
        "rewrite_menu": "rewrite_menu",
        "alert_kds": "alert_kds",
        END: END,
    })

    return builder.compile()


_proactive_graph = None

def get_proactive_graph():
    global _proactive_graph
    if _proactive_graph is None:
        _proactive_graph = build_proactive_graph()
    return _proactive_graph