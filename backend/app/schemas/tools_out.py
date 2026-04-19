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

class OpsState(BaseModel):
    active_staff_count: int
    pending_orders: int
    kitchen_load_percent: float

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

class FxRate(BaseModel):
    rate: float

class MarketData(BaseModel):
    oil: Optional[MarketIndicator] = None
    fx: Optional[FxRate] = None

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

class SupplyChainOption(BaseModel):
    supplier_id: str
    total_landed_cost: float
    reliability_index: float  # 0.0 - 1.0
    estimated_delivery: float # in hours

class EvaluateSupplyChainOptionsOutput(BaseModel):
    """Output for evaluate_supply_chain_options"""
    options: List[SupplyChainOption]

class CheckOperationalCapacityOutput(BaseModel):
    """Output for check_operational_capacity"""
    is_feasible: bool
    bottleneck_risk: Literal["high", "low"]
    recommended_staff_addition: int


# ==========================================
# Phase 3: Execution (Action) Outputs
# ==========================================

class ExecuteOperationalActionOutput(BaseModel):
    """Output for execute_operational_action"""
    status: Literal["success", "failed"]
    transaction_id: str
    updated_state_digest: str

class FormulateMarketingStrategyOutput(BaseModel):
    """Output for formulate_marketing_strategy"""
    campaign_id: str
    activation_timestamp: str
    estimated_reach: int

class SendHumanNotificationOutput(BaseModel):
    """Output for send_human_notification"""
    notification_id: str
    delivery_channel: Literal["admin_dashboard", "whatsapp"]


# ==========================================
# Phase 4: Evolution (Memory) Outputs
# ==========================================

class GeneratePostMortemLearningOutput(BaseModel):
    """Output for generate_post_mortem_learning"""
    lesson_learned: str
    embedding_id: str
    strategy_adjustment: str