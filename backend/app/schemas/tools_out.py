from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

# ==========================================
# Phase 1: Perception (Observation) Outputs
# ==========================================

class InventoryItemRisk(BaseModel):
    item_id: str
    name: str
    qty: float
    expiry_risk_score: float

class FinanceState(BaseModel):
    daily_revenue: float
    current_margin_avg: float
    burn_rate: float
    weekly_revenue: Optional[float] = None
    weekly_margin: Optional[float] = None
    inventory_total_value: Optional[float] = None

class OpsState(BaseModel):
    active_staff_count: int
    pending_orders: int
    kitchen_load_percent: float
    staff_shortage_risk: Optional[Literal["low", "medium", "high"]] = None
    bottleneck_role: Optional[str] = None

class GetBusinessStateOutput(BaseModel):
    """Output for get_business_state"""
    inventory: Optional[List[InventoryItemRisk]] = None
    finance: Optional[FinanceState] = None
    ops: Optional[OpsState] = None

class ExtractedEntities(BaseModel):
    item: Optional[str] = None
    price: Optional[float] = None
    date: Optional[str] = None
    supplier: Optional[str] = None

class ParseUnstructuredSignalOutput(BaseModel):
    """Output for parse_unstructured_signal"""
    intent: str
    entities: ExtractedEntities
    sentiment: Literal["urgent", "neutral", "negative"]
    autonomy_level: Literal["L1", "L2", "L3"] = "L2"

class MarketIndicator(BaseModel):
    value: float
    trend: Literal["up", "down"]
    volatility: Optional[float] = None          
    predicted_value: Optional[float] = None

class FxRate(BaseModel):
    rate: float

class MarketData(BaseModel):
    oil: Optional[MarketIndicator] = None
    fx: Optional[FxRate] = None
    inflation: Optional[MarketIndicator] = None

class QueryMacroContextOutput(BaseModel):
    """Output for query_macro_context"""
    market_data: MarketData


# ==========================================
# Phase 2: Reasoning & Simulation Outputs
# ==========================================

class SimulateYieldScenarioOutput(BaseModel):
    """Output for simulate_yield_scenario"""
    projected_revenue_change: float
    new_margin: float
    break_even_volume_increase: float
    projected_profit_change: Optional[float] = None
    recommended_action: Optional[str] = None
    elasticity_factor: Optional[float] = None

class SupplyChainOption(BaseModel):
    supplier_id: str
    total_landed_cost: float
    reliability_index: float  # 0.0 - 1.0
    estimated_delivery: float # in hours
    lead_time_risk: Optional[Literal["low", "medium", "high"]] = None
    historical_on_time_rate: Optional[float] = None

class EvaluateSupplyChainOptionsOutput(BaseModel):
    """Output for evaluate_supply_chain_options"""
    options: List[SupplyChainOption]

class CheckOperationalCapacityOutput(BaseModel):
    """Output for check_operational_capacity"""
    is_feasible: bool
    bottleneck_risk: Literal["high", "low"]
    recommended_staff_addition: int
    bottleneck_role: Optional[str] = None
    detail_analysis: Optional[str] = None


# ==========================================
# Phase 3: Execution (Action) Outputs
# ==========================================

class ExecuteOperationalActionOutput(BaseModel):
    """Output for execute_operational_action"""
    status: Literal["success", "failed", "pending_approval"]
    transaction_id: str
    updated_state_digest: str

class FormulateMarketingStrategyOutput(BaseModel):
    """Output for formulate_marketing_strategy"""
    campaign_id: str
    activation_timestamp: str
    estimated_reach: int
    estimated_roi: Optional[float] = None
    recommended_audience: Optional[str] = None

class SendHumanNotificationOutput(BaseModel):
    """Output for send_human_notification"""
    notification_id: str
    delivery_channel: Literal["admin_dashboard", "whatsapp", "email", "telegram"]


# ==========================================
# Phase 4: Evolution (Memory) Outputs
# ==========================================

class GeneratePostMortemLearningOutput(BaseModel):
    """Output for generate_post_mortem_learning"""
    lesson_learned: str
    embedding_id: str
    strategy_adjustment: str
    similarity_score: Optional[float] = None

class NewsArticle(BaseModel):
    headline: str
    impact_level: Literal["high", "medium", "low"]
    summary: str

class FetchMacroNewsOutput(BaseModel):
    """Output for fetch_macro_news"""
    articles: List[NewsArticle] 
    

# * Newly added
class IngredientDetail(BaseModel):
    qty: float
    item_name: str
class MenuItem(BaseModel):
    item_id: str
    name: str
    category: str
    current_price: float
    margin_percent: float
    is_available: bool
    ingredients: List[IngredientDetail] = []  # links back to inventory for stock checks
    # qty: number, item_name: string
 
class GetAllMenuItemsOutput(BaseModel):
    """Output for get_all_menu_items"""
    items: List[MenuItem]
    total_count: int
 
 
# ==========================================
# contact_supplier
# ==========================================
 
class ContactSupplierOutput(BaseModel):
    """Output for contact_supplier"""
    status: Literal["sent", "failed", "queued"]
    contact_log_id: str          # FK into supplier_contact_logs table
    supplier_name: str
    channel_used: Literal["email", "whatsapp", "sms", "logged_only"]
    message_preview: str         # first 120 chars of sent message
    expected_response_hrs: int   # SLA estimate based on supplier's avg_lead_time
 
 
# ==========================================
# save_to_kds_table
# ==========================================
 
class SaveToKdsOutput(BaseModel):
    """Output for save_to_kds"""
    kds_entry_id: str
    status: Literal["displayed", "queued", "failed"]
    eta_timestamp: str           # ISO timestamp = now + estimated_prep_minutes
    position_in_queue: int       # 1 = next up, higher = further back
 
 
# ==========================================
# get_all_orders
# ==========================================
 
class OrderRecord(BaseModel):
    order_id: str
    timestamp: str
    items: list                  # raw JSONB from DB
    total_revenue: float
    total_margin: float
    status: str
 
class GetAllOrdersOutput(BaseModel):
    """Output for get_all_orders"""
    orders: List[OrderRecord]
    total_revenue_sum: float
    total_count: int
 
 
# ==========================================
# get_festival_calendar
# ==========================================
 
class FestivalEvent(BaseModel):
    name: str
    date: str                    # ISO date
    days_away: int
    type: Literal["public_holiday", "religious", "cultural"]
    demand_impact: Optional[str] = None   # e.g. "+40% noodle dishes, -60% pork items"
    staffing_note: Optional[str] = None  # e.g. "Muslim staff may request leave"
 
class GetFestivalCalendarOutput(BaseModel):
    """Output for get_festival_calendar"""
    events: List[FestivalEvent]
    nearest_event_days_away: int
 
 
# ==========================================
# query_macro_context (upgraded)
# ==========================================
 
class MacroIndicatorLive(BaseModel):
    indicator: str
    value: Optional[float]       # None if only qualitative data available
    trend: Literal["up", "down", "stable"]
    confidence: Literal["high", "medium", "low"]
    news_summary: Optional[str]  # 1-sentence GLM digest of latest headline
    source_url: Optional[str]    # URL of the article used
 
class QueryMacroContextOutput(BaseModel):
    """Output for query_macro_context (upgraded — live news)"""
    results: List[MacroIndicatorLive]
    overall_risk_level: Literal["low", "elevated", "high"]
    agent_recommendation: str    # e.g. "Oil trending up — apply 15% logistics surcharge to all POs"