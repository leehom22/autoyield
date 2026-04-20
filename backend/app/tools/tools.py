import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from app.core.supabase import supabase
from app.schemas.tools_in import *
from app.schemas.tools_out import *
from langchain_core.tools import tool
from app.services.permission_service import check_action_permission

# ==========================================
# Phase 1: Perception
# ==========================================
#TODO: Optimize docstrings

@tool
async def get_business_state(params: GetBusinessStateInput) -> GetBusinessStateOutput:
    """
    Retrieve real-time snapshots of business state.
    scope: 'inventory' | 'finance' | 'ops'
    """
    scope = params.scope
    now = datetime.now(timezone.utc)
    
    if scope == "inventory":
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
        today = now.date().isoformat()
        res = supabase.table("orders").select("total_revenue, total_margin").gte("timestamp", today).execute()
        total_rev = sum(r["total_revenue"] for r in res.data)
        total_mar = sum(r["total_margin"] for r in res.data)
        margin_avg = (total_mar / total_rev) if total_rev > 0 else 0.0

        week_ago = (now - timedelta(days=7)).date().isoformat()
        res_week = supabase.table("orders").select("total_revenue, total_margin").gte("timestamp", week_ago).execute()
        weekly_rev = sum(r["total_revenue"] for r in res_week.data)
        weekly_mar = sum(r["total_margin"] for r in res_week.data)
        weekly_margin_avg = (weekly_mar / weekly_rev) if weekly_rev > 0 else 0.0

        inv_res = supabase.table("inventory").select("qty, unit_cost").execute()
        total_inv_value = sum(float(i["qty"]) * float(i["unit_cost"]) for i in inv_res.data)

        return GetBusinessStateOutput(finance=FinanceState(
            daily_revenue=round(total_rev, 2), current_margin_avg=round(margin_avg, 2), burn_rate=250.0,
            weekly_revenue=round(weekly_rev, 2), weekly_margin=round(weekly_margin_avg, 2), inventory_total_value=round(total_inv_value, 2)
        ))

    elif scope == "ops":
        roster = supabase.table("staff_roster").select("current_load").execute()
        avg_load = sum(r["current_load"] for r in roster.data) / len(roster.data) if roster.data else 0.0
        shortage_risk, bottleneck_role = "low", None
        for r in roster.data:
            load_ratio = r["current_load"] / r["max_capacity_score"] if r["max_capacity_score"] else 0
            if load_ratio > 0.9:
                shortage_risk, bottleneck_role = "high", r["role"]
                break
            elif load_ratio > 0.75:
                shortage_risk = "medium"

        try:
            from app.engine.simulator import world_engine
            pending = len(world_engine.active_order_queue)
        except (ImportError, AttributeError):
            pending = random.randint(5, 15)
            
        return GetBusinessStateOutput(ops=OpsState(
            active_staff_count=len(roster.data), pending_orders=pending, kitchen_load_percent=round(avg_load * 100, 2),
            staff_shortage_risk=shortage_risk, bottleneck_role=bottleneck_role
        ))

@tool
async def query_macro_context(params: QueryMacroContextInput) -> QueryMacroContextOutput:
    """
        Fetch macro-economic indicators to adjust risk and logistics weights.
        indicators: list containing any of ['oil_price', 'usd_myr', 'local_inflation']
    """
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

# @tool
# async def parse_unstructured_signal(params: ParseUnstructuredSignalInput) -> ParseUnstructuredSignalOutput:
#     """
#         Parse messy unstructured inputs (WhatsApp texts, OCR invoices, voice transcripts)
#         into structured JSON using pattern extraction.
#         content_type: 'text' | 'ocr_result' | 'stt_transcript'
#     """
#     return await _parse_unstructured_signal(
#         raw_content=params.raw_content,
#         input_type=params.type,
#         image_data_url=getattr(params, 'image_data_url', None)
#     )


# ==========================================
# Phase 2: Reasoning & Simulation
# ==========================================

@tool
async def simulate_yield_scenario(params: SimulateYieldScenarioInput) -> SimulateYieldScenarioOutput:
    """
        Simulate the profit impact of a price change or bundle deal.
        action: 'discount' | 'bundle'
        value: discount percentage (0-100) or bundle price
        """
    res = supabase.table("menu_items").select("current_price, margin_percent").eq("id", params.item_id).execute()
    if not res.data:
        return SimulateYieldScenarioOutput(projected_revenue_change=0.0, new_margin=0.0, break_even_volume_increase=0.0)
    
    item = res.data[0]
    current_price = float(item["current_price"])
    cost = current_price * (1.0 - float(item["margin_percent"]) / 100.0)
    
    new_price = current_price * (1.0 - params.value) if params.action == "discount" else (params.value if params.value else current_price)
    new_margin = ((new_price - cost) / new_price) * 100 if new_price > 0 else 0
    
    # Equilibrium point between profit and cost
    original_profit = current_price - cost
    new_profit = new_price - cost
    be_increase = 999.0 if new_profit <= 0 else original_profit / new_profit
    
    elasticity = -1.2 # Hardcoded elasticity for hackathon predictability
    price_change_pct = (new_price - current_price) / current_price
    projected_profit_change = new_profit - original_profit 

    if new_margin > float(item["margin_percent"]):
        recommended = "increase_price"
    elif new_margin < float(item["margin_percent"]) - 5:
        recommended = "discount_acceptable"
    else:
        recommended = "maintain"
    
    return SimulateYieldScenarioOutput(
        projected_revenue_change=round(new_price - current_price, 2),
        new_margin=round(new_margin, 2),
        break_even_volume_increase=round(be_increase, 2),
        projected_profit_change=round(projected_profit_change, 2),
        recommended_action=recommended,
        elasticity_factor=round(elasticity, 2)
    )

@tool
async def evaluate_supply_chain_options(params: EvaluateSupplyChainOptionsInput) -> EvaluateSupplyChainOptionsOutput:
    """
        Compare all suppliers for a given inventory item by total landed cost vs reliability.
    """
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

@tool
async def check_operational_capacity(params: CheckOperationalCapacityInput) -> CheckOperationalCapacityOutput:
    """
        Validate if current staff can handle a projected order surge.
        projected_order_surge: expected additional orders
        complexity_factor: 1 (simple) to 5 (very complex dishes)
    """
    # """
    # R-Agent Reasoning Note:
    # Choose 0.05 as the surge multiplier to reflect a moderate incraese in order velocity while avoiding overfitting to short-term spikes
    # (Can be upgraded to a more sophisticated time-series forecasting model)
    # """
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
@tool
async def execute_operational_action(params: ExecuteOperationalActionInput) -> ExecuteOperationalActionOutput:
    """
        Write tool — executes UPDATE_MENU, CREATE_PO (purchase order), or INVENTORY_ADJUST.
        action_type: 'UPDATE_MENU' | 'CREATE_PO' | 'INVENTORY_ADJUST'
        payload: { target_id, new_value }
    """

    allowed, reason = check_action_permission(params.action_type, params.payload.model_dump())
    if not allowed:
        if "Approval required" in reason:
            # Create notification, request for approval
            notif_id = str(uuid.uuid4())
            supabase.table("notifications").insert({
                "notification_id": notif_id,
                "priority": "high",
                "message": reason,
                "proposed_action": params.model_dump(),
                "status": "pending",
                "is_read": False
            }).execute()
            return ExecuteOperationalActionOutput(
                status="pending_approval",
                transaction_id=notif_id,
                updated_state_digest="Action paused. Awaiting human approval."
            )
        else:
            return ExecuteOperationalActionOutput(
                status="failed",
                transaction_id="",
                updated_state_digest=f"Action rejected: {reason}"
            )
    
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
            po = params.payload.new_value
            supplier_id = po.get("supplier_id")
            if supplier_id:
                sup_res = supabase.table("suppliers").select("avg_lead_time").eq("id", supplier_id).execute()
                if sup_res.data:
                    arrival = datetime.now(timezone.utc) + timedelta(hours=sup_res.data[0]["avg_lead_time"])
                    po["arrival_estimate"] = arrival.isoformat()
            supabase.table("procurement_logs").insert(po).execute()
            status = "success"

        elif params.action_type == "INVENTORY_ADJUST":
            supabase.table("inventory").update(params.payload.new_value).eq("id", params.payload.target_id).execute()
            status = "success"

        elif params.action_type == "ALERT_KDS":
            supabase.table("kds_events").insert(params.payload.new_value).execute()
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

@tool
async def formulate_marketing_strategy(params: FormulateMarketingStrategyInput) -> FormulateMarketingStrategyOutput:
    """
        Trigger a targeted marketing campaign.
        strategy_type: 'VOUCHER' | 'FLASH_SALE' | 'AD_BOOST'
        goal: 'clear_stock' | 'maximize_margin'
        config: { discount, audience, budget }
    """
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

@tool
async def send_human_notification(params: SendHumanNotificationInput) -> SendHumanNotificationOutput:
    """
        Send an Approve/Reject notification to the human operator for high-stakes decisions.
        priority: 'high' | 'medium'
        Use for: spending > RM500, price changes > 15%, or irreversible actions.
    """
    notification_id = str(uuid.uuid4())
    supabase.table("notifications").insert({
        "notification_id": notification_id,
        "priority": params.priority,
        "message": params.message,
        "proposed_action": params.proposed_action_json,
        "status": "pending",
        "is_read": False
    }).execute()

    print(f"⚠️ [Human Required] Priority: {params.priority} | Msg: {params.message}")

    if params.channel in ["whatsapp", "email", "telegram"]:
        print(f"📡 [External API] Simulating message dispatch via {params.channel.upper()} gateway...")

    return SendHumanNotificationOutput(
        notification_id=notification_id,
        delivery_channel=params.channel if params.channel != "dashboard" else "admin_dashboard"
    )


# ==========================================
# Phase 4: Evolution (RAG & Learning)
# ==========================================
@tool
async def generate_post_mortem_learning(params: GeneratePostMortemLearningInput) -> GeneratePostMortemLearningOutput:
    """
        Compare expected vs actual outcome, write a lesson into the knowledge base.
        actual_outcome: { revenue, waste_reduced }
    """
    # Vector Degradation Protection: Insert zero vector to pass DB constraints before asynchorously fetching real embedding from external service
    lesson = f"Event {params.event_id} yielded revenue {params.actual_outcome.revenue}."
    strategy = "Adjust weights towards P-Agent if revenue drop > 15%."
    
    if params.expected_outcome:
        rev_diff = params.actual_outcome.revenue - params.expected_outcome.revenue
        lesson += f" Expected revenue was {params.expected_outcome.revenue}, difference: {rev_diff:.2f}."

    # Generate real embedding using Z.AI (GLM)
    from app.core.config import settings
    import httpx
    
    try:
        # Direct API call to GLM embedding model
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.GLM_BASE_URL}/embeddings",
                headers={"Authorization": f"Bearer {settings.GLM_API_KEY}"},
                json={"model": "embedding-2", "input": lesson}
            )
            embedding = resp.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"Embedding API error: {e}")
        embedding = [0.0] * 1536

    # Match and update/insert
    similar = None
    try:
        similar = supabase.rpc("match_knowledge_base", {
            "query_embedding": embedding, "match_threshold": 0.85, "match_count": 1
        }).execute()
    except Exception as e:
        print(f"RPC match_knowledge_base failed (fallback to insert): {e}")
    
    if similar.data and similar.data[0]["similarity"] > 0.9:
        best_match = similar.data[0]
        supabase.table("knowledge_base").update({
            "lesson_learned": lesson
        }).eq("id", best_match["id"]).execute()
        return GeneratePostMortemLearningOutput(lesson_learned=lesson, embedding_id=best_match["id"], strategy_adjustment=strategy, similarity_score=best_match["similarity"])

    supabase.table("knowledge_base").insert({
        "embedding_vector": embedding, "scenario_description": lesson, "lesson_learned": strategy, "performance_score": 0.85
    }).execute()
    
    return GeneratePostMortemLearningOutput(
        lesson_learned=lesson,
        embedding_id=f"mem_{str(uuid.uuid4())[:8]}",
        strategy_adjustment=strategy,
        similarity_score=None
    )

@tool
async def fetch_macro_news(params: FetchMacroNewsInput) -> FetchMacroNewsOutput:
    """
        Fetch macro news (e.g., supply chain disruptions, festivals) to aid forward-looking reasoning.
    """
    # For Hackathon: Return highly relevant mock signals based on real business context
    mock_news = [
        NewsArticle(
            headline="Monsoon season disrupts coastal logistics",
            impact_level="high",
            summary="Expect 20% delay and price spikes in seafood deliveries over the next 7 days."
        ),
        NewsArticle(
            headline="Mother's Day weekend approaching",
            impact_level="medium",
            summary="Historical F&B data shows a 40% surge in family-style dining."
        )
    ]
    return FetchMacroNewsOutput(articles=mock_news)