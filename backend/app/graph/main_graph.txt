"""
IF User Unstructured Input -> 1. Supervisor node
IF God Mode -> 4. P and R agent
IF 7 days trigger for Report -> 4. P and R agent

# 1. Supervisor Node
- check completeness
- check intent
- decide path
IF invoice / any CRUD instrcution -> Clerk agent node
IF common query -> Call tools for analysis + Advise
IF profit and crisis -> P and R Agent node

# 2. Clerk Agent Node
- Invoice OCR extraction
- validate fields
- check price spike (tools)
IF price spike > 15% -> P and R agent node
IF missing info -> ask back user
IF info OK -> Database

# 3. P Agent and R Agent Node
- Debate
- Solutions proposed
- Judge Winner
-> Execution Node

# 4. Execution Node
- Tie -> Human notification
- Got winner -> Execution Tools / Database -> Lesson training

# ALL IF COMPLETE -> Reply User
"""

import asyncio
from typing import Annotated, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from app.services.invoice_extractor import extract_invoice_data
from app.services.invoice_crud import execute_invoice_crud
from app.services.db_service import get_inventory_status
from app.tools.tools import (
    get_business_state,
    query_macro_context,
    simulate_yield_scenario,
    evaluate_supply_chain_options,
    check_operational_capacity,
    execute_operational_action,
    formulate_marketing_strategy,
    send_human_notification,
)
from app.core.supabase import supabase

# Import P/R Agent Graph
try:
    from graph.graph import get_graph as get_pr_graph
    PR_GRAPH_AVAILABLE = True
except ImportError:
    PR_GRAPH_AVAILABLE = False
    print("⚠️ P/R Agent graph not available, using fallback")


# ==========================================
# States Definition
# ==========================================

class MainState(TypedDict):

    # Input
    raw_content: str
    input_type: Literal["text", "ocr_result", "stt_transcript"]
    image_data_url: Optional[str]
    source: Literal["user", "god_mode", "weekly_report"]
    
    # Parsing Results
    parsed_intent: Optional[str]
    parsed_entities: Optional[dict]
    parsed_autonomy: Optional[str]
    is_complete: bool
    missing_fields: list[str]
    
    # Route decision
    target_agent: Optional[Literal["clerk", "analyst", "pr_agent"]]
    
    # Clerk Agent State
    invoice_data: Optional[dict]
    price_spike_detected: bool
    clerk_result: Optional[dict]
    
    # Analyst Agent State
    analysis_result: Optional[str]
    
    # P/R Agent State
    debate_context: Optional[dict]
    debate_result: Optional[dict]
    
    # Execution Result
    execution_result: Optional[dict]
    final_response: str
    
    # Messages for P/R Agent
    messages: Annotated[list[BaseMessage], add_messages]


# ==========================================
# Entry Router Node
# ==========================================

def entry_router_node(state: MainState) -> MainState:
    
    source = state.get("source", "user")
    
    # God Mode and Report Request directly pass to P/R Agent
    if source in ["god_mode", "weekly_report"]:
        return {**state, "target_agent": "pr_agent"}
    
    # User input check completeness and intent first
    # Skip and no need parse_unstructured_signal
    
    intent = state.get("parsed_intent", "")
    is_complete = state.get("is_complete", True)
    
    # Missing Info → Query user for response
    if not is_complete:
        missing = state.get("missing_fields", [])
        state["final_response"] = f"Missing information: {', '.join(missing)}. Please provide these details."
        return {**state, "target_agent": None}
    
    # Invoice or CRUD Instrcution → Clerk Agent
    if intent in ["INVOICE", "PRICE_UPDATE", "CREATE_PO", "INVENTORY_ADJUST", "MENU_HIDE"]:
        return {**state, "target_agent": "clerk"}
    
    # Common consult → Analyst Agent
    if intent in ["WHAT_IF_ANALYSIS", "DATA_ANALYSIS", "FORECAST_REQUEST"]:
        return {**state, "target_agent": "analyst"}
    
    # Profit / Crisis → P/R Agent
    if intent in ["CLEAR_STOCK", "SUPPLY_DELAY", "PRICE_SPIKE_ALERT", "GENERAL_CRISIS"]:
        return {**state, "target_agent": "pr_agent"}
    
    # Default P/R Agent
    return {**state, "target_agent": "pr_agent"}


# ==========================================
# Clerk Agent Node
# ==========================================

async def clerk_agent_node(state: MainState) -> MainState:
    
    # 1. Retrieve invoice data via OCR if not done yet
    if not state.get("invoice_data"):
        if not state.get("image_data_url"):
            return {
                **state,
                "final_response": "No invoice image provided. Please upload an image.",
                "target_agent": None,
            }
        
        try:
            invoice_data = await extract_invoice_data(state["image_data_url"])
            state["invoice_data"] = invoice_data
        except Exception as e:
            return {
                **state,
                "final_response": f"Failed to extract invoice data: {e}",
                "target_agent": None,
            }
    
    invoice_data = state["invoice_data"]
    items = invoice_data.get("items", [])
    
    # 2. Check required fields
    missing = []
    if not invoice_data.get("supplier"):
        missing.append("supplier")
    for i, item in enumerate(items):
        if not item.get("name"):
            missing.append(f"item[{i}].name")
        if item.get("quantity") is None:
            missing.append(f"item[{i}].quantity")
        if item.get("unit_price") is None:
            missing.append(f"item[{i}].unit_price")
    
    # Query user for missing info
    if missing:
        return {
            **state,
            "is_complete": False,
            "missing_fields": missing,
            "final_response": f"Invoice missing: {', '.join(missing)}. Please provide these details.",
            "target_agent": None,
        }
    
    # 3. Check price spike against inventory historical cost
    price_spike_detected = False
    inv_items = get_inventory_status()
    
    for item in items:
        item_name = item.get("name")
        new_cost = item.get("unit_price")
        inv_item = next((i for i in inv_items if i["name"].lower() == item_name.lower()), None)
        if inv_item:
            current_cost = float(inv_item["unit_cost"])
            if new_cost > current_cost * 1.15:
                price_spike_detected = True
                break
    
    if price_spike_detected:
        # Trigger P/R Agent
        return {
            **state,
            "price_spike_detected": True,
            "debate_context": {
                "trigger": "INVOICE_PRICE_SPIKE",
                "items": items,
                "current_prices": {
                    item["name"]: next((i["unit_cost"] for i in inv_items if i["name"].lower() == item["name"].lower()), None)
                    for item in items
                },
            },
            "target_agent": "pr_agent",
        }
    
    # Store into DB 
    try:
        crud_result = await execute_invoice_crud(invoice_data)
        return {
            **state,
            "clerk_result": crud_result,
            "execution_result": crud_result,
            "final_response": f"Invoice processed successfully. PO created: {crud_result.get('purchase_order_ids', [])}",
            "target_agent": None,
        }
    except Exception as e:
        return {
            **state,
            "final_response": f"Failed to save invoice: {e}",
            "target_agent": None,
        }


# ==========================================
# Analyst Agent Node
# ==========================================

async def analyst_agent_node(state: MainState) -> MainState:
    """
    Analyst Agent: Call tools for analysis
    """

    result = "pass"   #TO-DO: implement analysis prompt and tool calls
    
    return {
        **state,
        "analysis_result": result,
        "final_response": result,
        "target_agent": None,
    }


# ==========================================
# P/R Agent Node
# ==========================================

async def pr_agent_node(state: MainState) -> MainState:

    if not PR_GRAPH_AVAILABLE:
        # Fallback
        return {
            **state,
            "final_response": "P/R Agent not available. Please check configuration.",
            "target_agent": None,
        }
    
    pr_graph = get_pr_graph()
    
    # Debate context
    debate_context = state.get("debate_context", {})
    trigger = debate_context.get("trigger", state.get("source", "user"))
    
    # Constrcut msg for P/R Agent
    if trigger == "INVOICE_PRICE_SPIKE":
        items = debate_context.get("items", [])
        message_content = f"Crisis detected: Price spike on invoice items: {items}. P-Agent and R-Agent debate required."
    elif state.get("source") == "god_mode":
        message_content = "God Mode crisis triggered. Analyze impact and propose actions."
    elif state.get("source") == "weekly_report":
        message_content = "Weekly procurement report analysis required. Review last 7 days of purchases."
    else:
        message_content = state.get("raw_content", "Please analyze this situation and propose actions.")
    
    # Call graph
    try:
        result = await pr_graph.ainvoke({
            "messages": [HumanMessage(content=message_content)],
        })
        
        final_response = result.get("final_response", "Decision made.")
        
        # Record decision logs
        supabase.table("decision_logs").insert({
            "trigger_signal": trigger,
            "p_agent_argument": result.get("p_agent_position", ""),
            "r_agent_argument": result.get("r_agent_position", ""),
            "resolution": "Debate completed",
            "action_taken": final_response[:500],
        }).execute()
        
        return {
            **state,
            "debate_result": result,
            "final_response": final_response,
            "target_agent": None,
        }
    except Exception as e:
        return {
            **state,
            "final_response": f"P/R Agent error: {e}",
            "target_agent": None,
        }


# ==========================================
# Router function
# ==========================================

def route_after_entry(state: MainState) -> Literal["clerk_agent", "analyst_agent", "pr_agent", "__end__"]:
    target = state.get("target_agent")
    if target == "clerk":
        return "clerk_agent"
    if target == "analyst":
        return "analyst_agent"
    if target == "pr_agent":
        return "pr_agent"
    return "__end__"


# ==========================================
# Construct Graph
# ==========================================

def build_main_graph():
    builder = StateGraph(MainState)
    
    # Add nodes
    builder.add_node("entry_router", entry_router_node)
    builder.add_node("clerk_agent", clerk_agent_node)
    builder.add_node("analyst_agent", analyst_agent_node)
    builder.add_node("pr_agent", pr_agent_node)
    
    # Add edges
    builder.add_edge(START, "entry_router")
    
    builder.add_conditional_edges(
        "entry_router",
        route_after_entry,
        {
            "clerk_agent": "clerk_agent",
            "analyst_agent": "analyst_agent",
            "pr_agent": "pr_agent",
            "__end__": END,
        }
    )
    
    # End after each agent node
    builder.add_edge("clerk_agent", END)
    builder.add_edge("analyst_agent", END)
    builder.add_edge("pr_agent", END)
    
    return builder.compile()


# Singleton
_main_graph = None

def get_main_graph():
    global _main_graph
    if _main_graph is None:
        _main_graph = build_main_graph()
    return _main_graph