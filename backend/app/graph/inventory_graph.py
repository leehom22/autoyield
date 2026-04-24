"""
ingestion_graph.py — Inventory Import Analysis flowchart
"""

from typing import Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
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
class IngestionState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # Set after price spike check
    price_spike_detected: bool        # True = >20% spike vs history
    spike_item_id: str                # inventory item that triggered
    spike_pct: float                  # how large the spike is (e.g. 0.35 = 35%)
    # Execution tracking
    supplier_contacted: bool
    action_logged: bool
    pending_handler: str
    final_response: str

# ─────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────
INGESTION_SUPERVISOR_PROMPT = """You are the Inventory Ingestion Agent.
A supplier invoice or stock update has just been parsed and handed to you.
Your job is to:
1. Call get_business_state(scope='inventory') to read current stock levels and unit costs.
2. Compare the parsed input price against the current unit_cost in the DB.
3. Determine if there is a price spike > 20% above the stored cost.
4. Route to the correct handling path based on your finding.
Always use tools to read live data — never assume prices from context."""


# ─────────────────────────────────────────────
# Node 1: Read current inventory state
# ─────────────────────────────────────────────
def read_inventory_node(state: IngestionState) -> IngestionState:
    """
    Calls get_business_state to get live inventory + unit costs.
    This is the 'Get input from database' step in the diagram.
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "get_business_state", "parse_unstructured_signal"
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = """Step 1: Read the current inventory state.
Call get_business_state(scope='inventory') to get all items with their current qty and unit costs.
Then review the parsed invoice/signal in the conversation history.
Identify which item the signal refers to and note its current stored unit_cost."""

    response = llm.invoke([SystemMessage(content=INGESTION_SUPERVISOR_PROMPT),
                           SystemMessage(content=prompt)] + state["messages"])
    return {**state, "messages": [response],"pending_handler" : "read_inventory"}


# ─────────────────────────────────────────────
# Node 2: Detect price spike
# ─────────────────────────────────────────────
def detect_spike_node(state: IngestionState) -> IngestionState:
    """
    Compares parsed invoice price vs DB unit_cost.
    Sets price_spike_detected, spike_item_id, spike_pct in state.
    """
    llm = get_glm()

    prompt = """Step 2: Price spike detection.
Based on the inventory data and the parsed signal in the conversation history:
- What item is being restocked/invoiced?
- What is the invoice price per unit?
- What is the current stored unit_cost for that item in the DB?
- Calculate: spike_pct = (invoice_price - unit_cost) / unit_cost
- Is spike_pct > 0.20 (i.e. >20%)?

Reply in this exact format (no other text):
ITEM_ID: <item_id>
INVOICE_PRICE: <float>
STORED_COST: <float>
SPIKE_PCT: <float>
SPIKE_DETECTED: <true|false>"""

    response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    content = response.content.strip()

    # Parse the structured reply
    spike_detected = False
    item_id = ""
    spike_pct = 0.0

    for line in content.splitlines():
        if line.startswith("SPIKE_DETECTED:"):
            spike_detected = "true" in line.lower()
        elif line.startswith("ITEM_ID:"):
            item_id = line.split(":", 1)[1].strip()
        elif line.startswith("SPIKE_PCT:"):
            try:
                spike_pct = float(line.split(":", 1)[1].strip())
            except ValueError:
                spike_pct = 0.0

    return {
        **state,
        "messages": [AIMessage(content=content)],
        "price_spike_detected": spike_detected,
        "spike_item_id": item_id,
        "spike_pct": spike_pct,
    }


# ─────────────────────────────────────────────
# Node 3a: Spike path — evaluate + simulate
# ─────────────────────────────────────────────
def spike_analysis_node(state: IngestionState) -> IngestionState:
    """
    Price spike confirmed. Runs:
    - evaluate_supply_chain_options → find cheaper alternative supplier
    - simulate_yield_scenario → quantify margin impact of switching vs absorbing cost
    Matches 'Evaluate Suppliers' + 'Simulate margin impact' in diagram.
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "evaluate_supply_chain_options", "simulate_yield_scenario", "get_all_menu_items"
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = f"""PRICE SPIKE DETECTED: {round(state['spike_pct'] * 100, 1)}% above stored cost.
Item: {state['spike_item_id']}

Follow this sequence:
1. Call evaluate_supply_chain_options(item_id='{state['spike_item_id']}') to find cheaper suppliers.
2. Call get_all_menu_items() to identify which menu items use this ingredient.
3. For each affected menu item, call simulate_yield_scenario to compare:
   a) Absorbing the new cost (lower margin)
   b) Switching supplier (different reliability/delivery tradeoff)
4. Summarise: which option preserves better margin? What is the projected impact?"""

    response = llm.invoke([SystemMessage(content=INGESTION_SUPERVISOR_PROMPT),
                           SystemMessage(content=prompt)] + state["messages"])
    return {**state, "messages": [response],"pending_handler" : "spike_analysis"}


# ─────────────────────────────────────────────
# Node 3b: No spike — normal restock
# ─────────────────────────────────────────────
def normal_restock_node(state: IngestionState) -> IngestionState:
    """
    No price spike. Simply update inventory qty via INVENTORY_ADJUST.
    Matches 'Update Inventory — Normal restock' in diagram.
    """
    tools = [t for t in get_all_lc_tools() if t.name in ["execute_operational_action"]]
    llm = get_glm().bind_tools(tools)

    prompt = """No price spike detected. Proceed with normal restock:
Call execute_operational_action with:
  action_type = 'INVENTORY_ADJUST'
  payload.target_id = the item_id from the invoice
  payload.new_value = { 'qty': <new_qty_from_invoice> }
  p_logic_summary = 'Normal restock — no price anomaly detected'
  r_logic_summary = 'Price within 20% of stored cost — safe to accept'"""

    response = llm.invoke([SystemMessage(content=INGESTION_SUPERVISOR_PROMPT),
                           SystemMessage(content=prompt)] + state["messages"])
    return {**state, "messages": [response],"pending_handler" : "normal_restock"}


# ─────────────────────────────────────────────
# Node 4: Notify operator + contact supplier
# ─────────────────────────────────────────────
def notify_and_contact_node(state: IngestionState) -> IngestionState:
    """
    After spike analysis: notify operator with findings, then contact the
    recommended alternative supplier.
    Matches 'Notify operator' + 'Email/WhatsApp/Telegram' in diagram.
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "send_human_notification", "contact_supplier"
    ]]
    llm = get_glm().bind_tools(tools)

    prompt = f"""Price spike of {round(state['spike_pct'] * 100, 1)}% confirmed for item {state['spike_item_id']}.

Step 1 — Notify operator:
Call send_human_notification with:
  priority = 'high'
  message = A full brief including: item name, spike %, current cost, invoice cost,
            recommended supplier switch with projected margin impact from simulation,
            and the proposed action awaiting approval.
  proposed_action_json = the CREATE_PO or supplier switch action

Step 2 — Contact alternative supplier (if analysis recommends switching):
Call contact_supplier with:
  message_type = 'price_inquiry' (if just checking) or 'purchase_order' (if approved path)
  Include: item name, required qty, required delivery date, your price ceiling."""

    response = llm.invoke([SystemMessage(content=INGESTION_SUPERVISOR_PROMPT),
                           SystemMessage(content=prompt)] + state["messages"])
    return {**state, "messages": [response], "supplier_contacted": True,"pending_handler" : "notify_and_contact"}


# ─────────────────────────────────────────────
# Node 5: Log decision + trace (both paths converge here)
# ─────────────────────────────────────────────
def log_decision_node(state: IngestionState) -> IngestionState:
    """
    Final node for both paths. Calls execute_operational_action (CREATE_PO or INVENTORY_ADJUST)
    and generate_post_mortem_learning to write the audit trail.
    Matches 'log decision + trace' + 'execute_operational_action (CREATE_PO)' in diagram.
    """
    tools = [t for t in get_all_lc_tools() if t.name in [
        "execute_operational_action", "generate_post_mortem_learning"
    ]]
    llm = get_glm().bind_tools(tools)

    if state["price_spike_detected"]:
        prompt = """Spike path finalization:
1. Call execute_operational_action with action_type='CREATE_PO' to log the purchase order
   to the recommended supplier. Include full p_logic_summary and r_logic_summary.
2. Call generate_post_mortem_learning with:
   event_id = the transaction_id from step 1
   actual_outcome = { 'revenue': 0.0, 'waste_reduced': 0.0 }
   (Revenue and waste impact will be updated after delivery is confirmed.)"""
    else:
        prompt = """Normal restock finalization:
The INVENTORY_ADJUST should already be done. Now call generate_post_mortem_learning with:
  event_id = the transaction_id from the INVENTORY_ADJUST
  actual_outcome = { 'revenue': 0.0, 'waste_reduced': 0.0 }
This closes the audit trail for this ingestion event."""

    response = llm.invoke([SystemMessage(content=INGESTION_SUPERVISOR_PROMPT),
                           SystemMessage(content=prompt)] + state["messages"])
    return {**state, "messages": [response], "action_logged": True, "pending_handler" : "log_decision"}


# ─────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────
def route_after_tools(state: IngestionState) -> str:
    handler = state.get("pending_handler", "read_inventory")

    if handler == "read_inventory":
        return "detect_spike"

    if handler == "spike_analysis":
        return "notify_and_contact"

    if handler == "normal_restock":
        return "log_decision"

    if handler == "notify_and_contact":
        return "log_decision"

    if handler == "log_decision":
        return END

    return END

def route_tools_ingestion(state: IngestionState) -> str:
    """Standard tool-call checker. Routes to tool_node if LLM requested tools."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return "__continue__"


def route_after_read(state: IngestionState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return "detect_spike"


def route_after_spike_detect(state: IngestionState) -> str:
    if state.get("price_spike_detected"):
        return "spike_analysis"
    return "normal_restock"


def route_after_spike_analysis(state: IngestionState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return "notify_and_contact"


def route_after_notify(state: IngestionState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return "log_decision"


def route_after_normal_restock(state: IngestionState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return "log_decision"


def route_after_log(state: IngestionState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END


# ─────────────────────────────────────────────
# Build graph
# ─────────────────────────────────────────────
def build_ingestion_graph():
    builder = StateGraph(IngestionState)

    builder.add_node("read_inventory", read_inventory_node)
    builder.add_node("detect_spike", detect_spike_node)
    builder.add_node("spike_analysis", spike_analysis_node)
    builder.add_node("normal_restock", normal_restock_node)
    builder.add_node("notify_and_contact", notify_and_contact_node)
    builder.add_node("log_decision", log_decision_node)
    builder.add_node("tool_node", ToolNode(get_all_lc_tools()))

    builder.add_edge(START, "read_inventory")

    builder.add_conditional_edges("read_inventory", route_after_read, {
        "tool_node": "tool_node",
        "detect_spike": "detect_spike",
    })

    builder.add_conditional_edges("tool_node", route_after_tools, {
        "detect_spike": "detect_spike",
        "notify_and_contact": "notify_and_contact",
        "log_decision": "log_decision",
        END: END,
    })

    builder.add_conditional_edges("detect_spike", route_after_spike_detect, {
        "spike_analysis": "spike_analysis",
        "normal_restock": "normal_restock",
    })

    builder.add_conditional_edges("spike_analysis", route_after_spike_analysis, {
        "tool_node": "tool_node",
        "notify_and_contact": "notify_and_contact",
    })

    builder.add_conditional_edges("normal_restock", route_after_normal_restock, {
        "tool_node": "tool_node",
        "log_decision": "log_decision",
    })

    builder.add_conditional_edges("notify_and_contact", route_after_notify, {
        "tool_node": "tool_node",
        "log_decision": "log_decision",
    })

    builder.add_conditional_edges("log_decision", route_after_log, {
        "tool_node": "tool_node",
        END: END,
    })

    return builder.compile()


_ingestion_graph = None

def get_ingestion_graph():
    global _ingestion_graph
    if _ingestion_graph is None:
        _ingestion_graph = build_ingestion_graph()
    return _ingestion_graph