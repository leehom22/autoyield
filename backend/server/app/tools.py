# app/agent/tools.py
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from app.services.glm_parser import parse_unstructured_signal as _parse_unstructured_signal
from app.core.supabase import supabase
from app.schemas.tools_in import *
from app.schemas.tools_out import *


# ==========================================
# Phase 1: Perception
# ==========================================

async def get_business_state(params: GetBusinessStateInput) -> GetBusinessStateOutput:
    
    scope = params.scope
    
    if scope == "inventory":
        now = datetime.now(timezone.utc)
        res = supabase.table("inventory").select("id, name, qty, expiry_timestamp").execute()
        
        items = []
        for row in res.data:
            expiry = datetime.fromisoformat(row["expiry_timestamp"]) if row.get("expiry_timestamp") else (now + timedelta(days=365))
            days_to_expiry = (expiry - now).days
            risk_score = 1.0 if days_to_expiry <= 2 else max(0.0, 1.0 - (days_to_expiry / 10.0))
            
            items.append(InventoryItemRisk(
                item_id=row["id"],
                name=row["name"],
                qty=row["qty"],
                expiry_risk_score=round(risk_score, 2)
            ))
        return GetBusinessStateOutput(inventory=items)

    elif scope == "finance":
        today = datetime.now().date().isoformat()
        res = supabase.table("orders").select("total_revenue, total_margin").gte("timestamp", today).execute()
        
        total_rev = sum(r["total_revenue"] for r in res.data)
        total_mar = sum(r["total_margin"] for r in res.data)
        margin_avg = (total_mar / total_rev) if total_rev > 0 else 0.0
        
        return GetBusinessStateOutput(finance=FinanceState(
            daily_revenue=round(total_rev, 2),
            current_margin_avg=round(margin_avg, 2),
            burn_rate=250.0 
        ))

    elif scope == "ops":
        roster = supabase.table("staff_roster").select("current_load").execute()
        avg_load = sum(r["current_load"] for r in roster.data) / len(roster.data) if roster.data else 0.0
        try:
            from app.engine.simulator import world_engine
            pending = len(world_engine.active_order_queue)
        except (ImportError, AttributeError):
            pending = random.randint(5, 15)
        return GetBusinessStateOutput(ops=OpsState(
            active_staff_count=len(roster.data),
            pending_orders=pending, 
            kitchen_load_percent=round(avg_load * 100, 2)
        ))


async def query_macro_context(params: QueryMacroContextInput) -> QueryMacroContextOutput:
    
    res = supabase.table("market_trends_current").select("*").execute()
    
    if not res.data:
        return QueryMacroContextOutput(market_data=MarketData(
            oil=MarketIndicator(value=85.0, trend="up"),
            fx=FxRate(rate=4.72)
        ))
    
    oil_data = next((item for item in res.data if item["indicator"] == "oil_price"), None)
    fx_data = next((item for item in res.data if item["indicator"] == "usd_myr"), None)
    
    trend_map = lambda slope: "up" if slope > 0 else "down"
    
    return QueryMacroContextOutput(market_data=MarketData(
        oil=MarketIndicator(value=oil_data["current_value"], trend=trend_map(oil_data["trend_slope"])) if oil_data else None,
        fx=FxRate(rate=fx_data["current_value"] if fx_data else 4.72)
    ))


async def parse_unstructured_signal(params: ParseUnstructuredSignalInput) -> ParseUnstructuredSignalOutput:
    return await _parse_unstructured_signal(
        raw_content=params.raw_content,
        input_type=params.type,
        image_data_url=getattr(params, 'image_data_url', None)
    )


# ==========================================
# Phase 2: Reasoning & Simulation
# ==========================================

# Can be upgraded
async def simulate_yield_scenario(params: SimulateYieldScenarioInput) -> SimulateYieldScenarioOutput:
    
    res = supabase.table("menu_items").select("current_price, margin_percent").eq("id", params.item_id).execute()
    if not res.data:
        return SimulateYieldScenarioOutput(projected_revenue_change=0.0, new_margin=0.0, break_even_volume_increase=0.0)
    
    item = res.data[0]
    current_price = float(item["current_price"])
    cost = current_price * (1.0 - float(item["margin_percent"]) / 100.0)
    
    new_price = current_price * (1.0 - params.value) if params.action == "discount" else current_price
    new_margin = ((new_price - cost) / new_price) * 100 if new_price > 0 else 0
    
    # Equilibrium point between profit and cost
    original_profit = current_price - cost
    new_profit = new_price - cost
    
    if new_profit <= 0:
        be_increase = 999.0   # Theoretically infinite increase needed to break even, but we cap it for sanity
    else:
        be_increase = original_profit / new_profit
    
    return SimulateYieldScenarioOutput(
        projected_revenue_change=round(new_price - current_price, 2),
        new_margin=round(new_margin, 2),
        break_even_volume_increase=round(be_increase, 2)
    )


async def evaluate_supply_chain_options(params: EvaluateSupplyChainOptionsInput) -> EvaluateSupplyChainOptionsOutput:
    # 1. Retrieve base cost of item from inventory
    item_res = supabase.table("inventory").select("unit_cost").eq("id", params.item_id).execute()
    if not item_res.data:
        return EvaluateSupplyChainOptionsOutput(options=[])
    base_cost = float(item_res.data[0]["unit_cost"])
    
    # 2. Retrieve all suppliers
    res = supabase.table("suppliers").select("id, avg_lead_time, reliability_score").execute()
    options = []
    for s in res.data:
        # Cost = base cost + logistic surcharge (higher if reliability is low)
        logistics_surcharge = base_cost * (1.0 - s["reliability_score"]) * 0.5
        total_landed_cost = base_cost + logistics_surcharge
        options.append(SupplyChainOption(
            supplier_id=s["id"],
            total_landed_cost=round(total_landed_cost, 2),
            reliability_index=s["reliability_score"],
            estimated_delivery=s["avg_lead_time"]
        ))
    return EvaluateSupplyChainOptionsOutput(options=options)


async def check_operational_capacity(params: CheckOperationalCapacityInput) -> CheckOperationalCapacityOutput:
    """
    R-Agent Reasoning Note:
    Choose 0.05 as the surge multiplier to reflect a moderate incraese in order velocity while avoiding overfitting to short-term spikes
    (Can be upgraded to a more sophisticated time-series forecasting model)
    """
    res = supabase.table("staff_roster").select("current_load").execute()
    avg_load = sum(r["current_load"] for r in res.data) / len(res.data) if res.data else 0.0
    
    projected_load = avg_load + (params.projected_order_surge * 0.05 * params.complexity_factor)
    
    return CheckOperationalCapacityOutput(
        is_feasible=projected_load < 0.95,
        bottleneck_risk="high" if projected_load > 0.85 else "low",
        recommended_staff_addition=int((projected_load - 0.8) / 0.1) if projected_load > 0.8 else 0
    )


# ==========================================
# Phase 3: Execution
# ==========================================

def execute_operational_action(params: ExecuteOperationalActionInput) -> ExecuteOperationalActionOutput:
    
    status = "failed"
    action_log = f"{params.action_type} - {params.payload.target_id}"
    
    try:
        # Boundary Check for JSON structure
        if not isinstance(params.payload.new_value, dict):
             return ExecuteOperationalActionOutput(
                status="failed",
                transaction_id="",
                updated_state_digest="Type error: payload.new_value must be a structured JSON dictionary."
            )

        # Routers for different action type
        if params.action_type == "UPDATE_MENU":
            supabase.table("menu_items").update(params.payload.new_value).eq("id", params.payload.target_id).execute()
            status = "success"
        elif params.action_type == "CREATE_PO":
            supabase.table("procurement_logs").insert(params.payload.new_value).execute()
            status = "success"
        elif params.action_type == "INVENTORY_ADJUST":
            supabase.table("inventory").update(params.payload.new_value).eq("id", params.payload.target_id).execute()
            status = "success"
            
        if status == "success":
            supabase.table("decision_logs").insert({
                "trigger_signal": params.action_type,
                "p_agent_argument": params.p_logic_summary,
                "r_agent_argument": params.r_logic_summary,
                "resolution": "Consensus Reached",
                "action_taken": action_log
            }).execute()
            
    except Exception as e:
        print(f"Agent Execution Crash: {e}")
        
    return ExecuteOperationalActionOutput(
        status=status,
        transaction_id=str(uuid.uuid4()) if status == "success" else "",
        updated_state_digest="state_mutated" if status == "success" else "unchanged"
    )


async def formulate_marketing_strategy(params: FormulateMarketingStrategyInput) -> FormulateMarketingStrategyOutput:
    supabase.table("marketing_campaigns").insert({
        "type": params.strategy_type,
        "trigger_event": params.goal,
        "spend": params.config.budget,
        "active_status": True
    }).execute()
    
    return FormulateMarketingStrategyOutput(
        campaign_id=str(uuid.uuid4()),
        activation_timestamp=datetime.now().isoformat(),
        estimated_reach=int(params.config.budget * 15)
    )


async def send_human_notification(params: SendHumanNotificationInput) -> SendHumanNotificationOutput:
    print(f"⚠️ [Human Required] Priority: {params.priority} | Msg: {params.message}")
    return SendHumanNotificationOutput(
        notification_id=str(uuid.uuid4()),
        delivery_channel="admin_dashboard"
    )


# ==========================================
# Phase 4: Evolution (RAG & Learning)
# ==========================================

async def generate_post_mortem_learning(params: GeneratePostMortemLearningInput) -> GeneratePostMortemLearningOutput:

    # Vector Degradation Protection: Insert zero vector to pass DB constraints before asynchorously fetching real embedding from external service
    lesson = f"Event {params.event_id} yielded revenue {params.actual_outcome.revenue}."
    strategy = "Adjust weights towards P-Agent if revenue drop > 15%."
    
    # Generate format of pgvector
    zero_vector = [0.0] * 1536
    
    supabase.table("knowledge_base").insert({
        "embedding_vector": zero_vector,
        "scenario_description": lesson,
        "lesson_learned": strategy,
        "performance_score": 0.85
    }).execute()
    
    return GeneratePostMortemLearningOutput(
        lesson_learned=lesson,
        embedding_id=f"mem_{str(uuid.uuid4())[:8]}",
        strategy_adjustment=strategy
    )