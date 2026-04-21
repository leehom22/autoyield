from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

# ==========================================
# Phase 1: Perception (Observation)
# ==========================================

class GetBusinessStateInput(BaseModel):
    """Retrieves real-time snapshots of inventory health, profit margins, and active staff load."""
    scope: Literal["inventory", "finance", "ops"] = Field(
        ..., description="The scope of business state to retrieve."
    ) 

class ParseUnstructuredSignalInput(BaseModel):
    """Uses GLM to extract intent, dates, and prices from messy inputs."""
    raw_content: str = Field(..., description="The raw unstructured text.") 
    type: Literal["text", "ocr_result", "stt_transcript"] = Field(
        ..., description="The type of the unstructured input."
    ) 
    image_data_url: Optional[str] = Field(None, description="Data URL of the image (if type is ocr_result)")

class QueryMacroContextInput(BaseModel):
    """Fetches oil prices and currency trends to adjust weights."""
    indicators: List[Literal["oil_price", "usd_myr", "local_inflation"]] = Field(
        ..., description="List of macro indicators to query."
    ) 


# ==========================================
# Phase 2: Reasoning & Simulation (The Debate)
# ==========================================

class SimulateYieldScenarioInput(BaseModel):
    """A Sandboxed calculator for the P-Agent to estimate the profit impact."""
    item_id: str = Field(..., description="Target menu item ID.") 
    action: Literal["discount", "bundle"] = Field(..., description="Action to simulate.") 
    value: float = Field(..., description="Numerical value for the action (e.g., discount percentage).") 
    bundle_items: Optional[List[str]] = Field(None, description="List of item IDs for bundle")

class EvaluateSupplyChainOptionsInput(BaseModel):
    """Compares different suppliers based on unit_cost vs. reliability_score + logistics_surcharge. [cite: 37]"""
    item_id: str = Field(..., description="Target inventory item ID to evaluate.") 

class CheckOperationalCapacityInput(BaseModel):
    """Validates if the current staff_roster can handle the projected surge."""
    projected_order_surge: float = Field(..., description="Estimated increase in order volume.") 
    complexity_factor: int = Field(..., ge=1, le=5, description="Complexity of the new menu/campaign (1-5).") 


# ==========================================
# Phase 3: Execution (Action)
# ==========================================

class ActionPayload(BaseModel):
    target_id: str 
    new_value: Any

class ExecuteOperationalActionInput(BaseModel):
    """The primary write-tool for UPDATE_MENU, CREATE_PURCHASE_ORDER, or INVENTORY_CORRECTION."""
    action_type: Literal["UPDATE_MENU", "CREATE_PO", "INVENTORY_ADJUST", "ALERT_KDS"]
    payload: ActionPayload 
    p_logic_summary: str = Field(..., description="Reasoning trace from P-Agent.") 
    r_logic_summary: str = Field(..., description="Reasoning trace from R-Agent.") 

class MarketingConfig(BaseModel):
    discount: float 
    audience: str 
    budget: float 

class FormulateMarketingStrategyInput(BaseModel):
    """Triggers targeted interventions."""
    strategy_type: Literal["VOUCHER", "FLASH_SALE", "AD_BOOST"] 
    config: MarketingConfig 
    goal: Literal["clear_stock", "maximize_margin"] 

class SendHumanNotificationInput(BaseModel):
    """Requests Approve/Reject for high-stakes decisions."""
    priority: Literal["high", "medium"] 
    message: str = Field(..., description="Explanation to the human manager.") 
    proposed_action_json: Dict[str, Any] = Field(..., description="The action awaiting approval.")
    channel: Optional[Literal["dashboard", "email", "whatsapp", "telegram"]] = Field(
        default="dashboard", description="Delivery channel for the notification."
    ) 


# ==========================================
# Phase 4: Evolution (Memory)
# ==========================================

class ActualOutcome(BaseModel):
    revenue: float 
    waste_reduced: float 

class GeneratePostMortemLearningInput(BaseModel):
    """Compares expected_yield vs. actual_yield and writes the Lesson."""
    event_id: str = Field(..., description="The ID of the decision/campaign being evaluated.") 
    actual_outcome: ActualOutcome
    expected_outcome: Optional['ActualOutcome'] = None

class FetchMacroNewsInput(BaseModel):
    """Fetches real-time macro news and festival context."""
    query: str = Field(..., description="Keywords for news search (e.g., 'seafood supply', 'upcoming festivals')")
    
    
# * Newly added tools

# ==========================================
# get_all_menu_items
# ==========================================

class GetAllMenuItemsInput(BaseModel):
    """Retrieves the full active menu with pricing and margin data."""
    filter_category: Optional[str] = Field(
        None,
        description="Optional category filter e.g. 'mains', 'drinks', 'desserts'. Omit to get all."
    )
    include_unavailable: bool = Field(
        False,
        description="Set True to include items currently marked unavailable. Default False."
    )


# ==========================================
# contact_supplier
# ==========================================

class ContactSupplierInput(BaseModel):
    """
    Send a structured message to a supplier.
    Use for: purchase order requests, price negotiation, delivery rescheduling,
    or emergency restock requests triggered by a stock crisis.
    """
    supplier_id: str = Field(..., description="Supplier ID from evaluate_supply_chain_options output.")
    message_type: Literal["purchase_order", "price_inquiry", "delivery_reschedule", "emergency_restock"] = Field(
        ..., description="The intent of this contact."
    )
    message_body: str = Field(
        ...,
        description="The full message to send. Be specific: include item name, qty, required delivery date, and any price constraints."
    )
    proposed_qty: Optional[float] = Field(None, description="Quantity to order (required for purchase_order and emergency_restock).")
    proposed_unit_price: Optional[float] = Field(None, description="Target unit price in RM (used for price_inquiry and negotiation).")


# ==========================================
# save_to_kds_table
# ==========================================

class KdsOrderItem(BaseModel):
    menu_item_id: str
    menu_item_name: str
    qty: int
    special_instructions: Optional[str] = None

class SaveToKdsInput(BaseModel):
    """
    Push an order or kitchen instruction to the Kitchen Display System (KDS).
    Use when: a surge resequences active orders, a menu item is swapped due to stock depletion,
    or the agent needs to alert the kitchen with updated ETAs.
    """
    order_id: str = Field(..., description="The order ID this KDS entry belongs to.")
    table_number: Optional[str] = Field(None, description="Table or delivery slot identifier.")
    items: List[KdsOrderItem] = Field(..., description="List of items to display on the KDS.")
    priority: Literal["normal", "urgent", "hold"] = Field(
        "normal",
        description="normal=standard queue | urgent=move to front | hold=pause until further notice"
    )
    estimated_prep_minutes: int = Field(
        ...,
        description="Agent-estimated prep time in minutes. Used to set ETA displayed to staff."
    )
    agent_note: Optional[str] = Field(
        None,
        description="Optional note from agent to kitchen staff e.g. 'Swap salmon for sea bass — stock depleted'."
    )


# ==========================================
# get_all_orders
# ==========================================

class GetAllOrdersInput(BaseModel):
    """
    Retrieve order records for analysis, demand forecasting, or post-mortem review.
    Used by the Demand Forecasting Loop to read historical order patterns.
    """
    status_filter: Optional[Literal["pending", "completed", "cancelled"]] = Field(
        None, description="Filter by order status. Omit to get all statuses."
    )
    date_from: Optional[str] = Field(
        None, description="ISO date string e.g. '2025-01-01'. Filters orders from this date."
    )
    date_to: Optional[str] = Field(
        None, description="ISO date string e.g. '2025-01-31'. Filters orders up to this date."
    )
    limit: int = Field(
        100,
        description="Max number of records to return. Use lower values for recent-only queries."
    )


# ==========================================
# get_festival_calendar
# ==========================================

class GetFestivalCalendarInput(BaseModel):
    """
    Retrieve upcoming Malaysian public holidays and major festivals within a date window.
    Use before demand forecasting — festivals cause predictable sales spikes (Hari Raya,
    Chinese New Year) or drops (fasting month lunch service) that must be factored into
    reorder triggers and staffing decisions.
    """
    days_ahead: int = Field(
        14,
        description="How many days ahead to look. Default 14. Use 30 for monthly planning."
    )
    include_food_impact: bool = Field(
        True,
        description="If True, returns expected demand_impact per festival (e.g. +40% noodles during CNY)."
    )


# ==========================================
# query_macro_context (upgraded)
# ==========================================

class QueryMacroContextInput(BaseModel):
    """
    Fetch real-world macro-economic signals via live news and financial data.
    Replaces the previous static DB version. Now searches for current headlines
    and derives trend signals from them.
    """
    indicators: List[Literal["oil_price", "usd_myr", "local_inflation"]] = Field(
        ..., description="Which indicators to fetch."
    )
    include_news_summary: bool = Field(
        True,
        description="If True, returns a 1-sentence GLM summary of the most relevant recent news headline per indicator."
    )