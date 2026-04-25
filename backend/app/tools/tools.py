import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import postgrest.exceptions
import httpx

from app.core.supabase import supabase
from app.core.config import settings
from app.schemas.tools_in import *
from app.schemas.tools_out import *
from langchain_core.tools import tool
from app.services.permission_service import check_action_permission
from app.engine.simulator import get_current_simulated_time
from app.core.glm_client import glm_client

# ==========================================
# Phase 1: Perception
# ==========================================
#TODO: Optimize docstrings
#TODO: Add tools: get_all_menu_items, contact_supplier, save_to_kds_table, get_all_orders, get_festival_calender, query_macro_context (get news, festival calendar, inflation data)


@tool
async def get_business_state(params: GetBusinessStateInput) -> GetBusinessStateOutput:
    """
    Retrieves real-time operational, financial, or inventory data from the restaurant's 
    core engine to assist in decision-making and risk assessment.

    Use this tool when you need to answer questions about the current status of the 
    restaurant's resources, performance, or potential bottlenecks.

    Args:
        params (GetBusinessStateInput): Contains the 'scope' which determines the type of data:
            - 'inventory': Returns a list of stock items with 'expiry_risk_score'. 
              A score of 1.0 indicates high risk (expires in <= 2 days). Use this to 
              identify ingredients that need to be used immediately or discarded.
            - 'finance': Provides a snapshot of daily/weekly revenue, margin averages, 
              and total inventory value. Use this to assess profitability or detect 
              abnormal burn rates.
            - 'ops': Returns current staffing levels, pending order counts, and kitchen load. 
              Crucial for identifying 'bottleneck_roles' and 'staff_shortage_risk' 
              during peak hours or festival events.

    Returns:
        GetBusinessStateOutput: A structured response containing the requested state data.
        All financial figures are rounded to 2 decimal places. Load percentages represent 
        the ratio of active tasks to staff capacity.
    """
    from app.engine.simulator import get_current_simulated_time

    scope = params.scope
    sim_now = get_current_simulated_time()
    
    if scope == "inventory":
        res = supabase.table("inventory").select("id, name, qty, expiry_timestamp").execute()
        
        items = []
        for row in res.data:
            expiry = datetime.fromisoformat(row["expiry_timestamp"]) if row.get("expiry_timestamp") else (sim_now + timedelta(days=365))
            days_to_expiry = (expiry - sim_now).days
            risk_score = 1.0 if days_to_expiry <= 2 else max(0.0, 1.0 - (days_to_expiry / 10.0))
            
            items.append(InventoryItemRisk(
                item_id=row["id"],
                name=row["name"],
                qty=row["qty"],
                expiry_risk_score=round(risk_score, 2)
            ))
        return GetBusinessStateOutput(inventory=items)

    elif scope == "finance":
        today = sim_now.date().isoformat()
        res = supabase.table("orders").select("total_revenue, total_margin").gte("timestamp", today).execute()
        total_rev = sum(r["total_revenue"] for r in res.data)
        total_mar = sum(r["total_margin"] for r in res.data)
        margin_avg = (total_mar / total_rev) if total_rev > 0 else 0.0

        week_ago = (sim_now - timedelta(days=7)).date().isoformat()
        res_week = supabase.table("orders").select("total_revenue, total_margin").gte("timestamp", week_ago).execute()
        weekly_rev = sum(r["total_revenue"] for r in res_week.data)
        weekly_mar = sum(r["total_margin"] for r in res_week.data)
        weekly_margin_avg = (weekly_mar / weekly_rev) if weekly_rev > 0 else 0.0

        inv_res = supabase.table("inventory").select("qty, unit_cost").execute()
        total_inv_value = sum(float(i["qty"]) * float(i["unit_cost"]) for i in inv_res.data)

        return GetBusinessStateOutput(finance=FinanceState(
            daily_revenue=round(total_rev, 2), current_margin_avg=round(margin_avg, 2), burn_rate=settings.DEFAULT_BURN_RATE,
            weekly_revenue=round(weekly_rev, 2), weekly_margin=round(weekly_margin_avg, 2), inventory_total_value=round(total_inv_value, 2)
        ))

    elif scope == "ops":
        roster = supabase.table("staff_roster").select("current_load").execute()
        avg_load = sum(r["current_load"] for r in roster.data) / len(roster.data) if roster.data else 0.0
        shortage_risk, bottleneck_role = "low", None
        for r in roster.data:
            # Safely fetch values with defaults (0 for load, 1 for capacity to avoid division by zero)
            current_load = r.get("current_load", 0)
            max_capacity = r.get("max_capacity_score", 1) # Default to 1 to avoid DivisionByZero

            load_ratio = current_load / max_capacity if max_capacity else 0
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

# @tool
# async def query_macro_context(params: QueryMacroContextInput) -> QueryMacroContextOutput:
#     """
#         Fetch macro-economic indicators to adjust risk and logistics weights.
#         indicators: list containing any of ['oil_price', 'usd_myr', 'local_inflation']
#     """
#     res = supabase.table("market_trends_current").select("*").execute()
    
#     if not res.data:
#         return QueryMacroContextOutput(market_data=MarketData(
#             oil=MarketIndicator(value=85.0, trend="up"),
#             fx=FxRate(rate=4.72)
#         ))
    
#     oil_data = next((item for item in res.data if item["indicator"] == "oil_price"), None)
#     fx_data = next((item for item in res.data if item["indicator"] == "usd_myr"), None)
    
#     trend_map = lambda slope: "up" if slope > 0 else "down"
    
#     return QueryMacroContextOutput(market_data=MarketData(
#         oil=MarketIndicator(value=oil_data["current_value"], trend=trend_map(oil_data["trend_slope"])) if oil_data else None,
#         fx=FxRate(rate=fx_data["current_value"] if fx_data else 4.72)
#     ))

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
    Simulates the financial impact of pricing strategies (discounts or bundles) on a specific menu item.
    
    Use this tool to perform 'What-If' analysis before changing prices. It helps determine if a 
    volume increase can offset a lower margin.
    
    Args:
        params (SimulateYieldScenarioInput):
            - item_id: The ID of the menu item to analyze.
            - action: 'discount' (percentage-based) or 'bundle' (fixed price point).
            - value: If action is 'discount', use 0.0-1.0 (e.g., 0.2 for 20% off). 
                     If 'bundle', use the total target price.
    
    Returns:
        A recommendation based on profit maintenance. 'break_even_volume_increase' 
        indicates how many more units must be sold to maintain the current profit level.
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
    
    elasticity = settings.DEFAULT_ELASTICITY   # Hardcoded elasticity for hackathon predictability
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
async def evaluate_supply_chain_options(params: EvaluateSupplyChainOptionsInput) -> str: # Return a string for better LLM parsing
    """
    Compares available suppliers for an inventory item. 
    Returns ranked options with Supplier Names, Costs, and Reliability.
    """
    # 1. Retrieve base cost
    try:
        item_res = supabase.table("inventory").select("unit_cost").eq("id", params.item_id).execute()
        if not item_res.data:
            return f"Error: Item ID {params.item_id} not found in inventory."
        base_cost = float(item_res.data[0]["unit_cost"])
    except Exception as e:
        return f"Database Error: {str(e)}"

    # 2. Retrieve suppliers (Added 'name' to the select!)
    # Tip: In a real app, you'd join with a 'supplier_items' table here
    res = supabase.table("suppliers").select("id, name, avg_lead_time, reliability_score").execute()
    
    if not res.data:
        return "No suppliers found in the database."

    processed_options = []
    for s in res.data:
        # Logistic surcharge calculation
        logistics_surcharge = base_cost * (1.0 - s["reliability_score"]) * 1.5 # Using a constant or settings
        total_landed_cost = base_cost + logistics_surcharge
        
        processed_options.append({
            "supplier_name": s["name"],
            "supplier_id": s["id"],
            "total_cost_rm": round(total_landed_cost, 2),
            "reliability": f"{int(s['reliability_score'] * 100)}%",
            "lead_time_days": s["avg_lead_time"]
        })

    # Sort by cost (cheapest first)
    processed_options.sort(key=lambda x: x["total_cost_rm"])

    # 3. Return as a clean, readable string/JSON
    import json
    return json.dumps(processed_options[:5]) # Limit to top 5 to prevent context overflow
# @tool
# async def evaluate_supply_chain_options(params: EvaluateSupplyChainOptionsInput) -> EvaluateSupplyChainOptionsOutput:
#     """
#     Compares available suppliers for an inventory item based on 'Total Landed Cost' and Reliability.
    
#     Use this tool when inventory is low or when the 'finance' scope indicates high burn rates.
#     It calculates a logistics surcharge based on a supplier's reliability score to provide 
#     the true cost of procurement.
    
#     Args:
#         params (EvaluateSupplyChainOptionsInput): The unique item_id from the inventory table.
        
#     Returns:
#         A list of options ranked by cost. High reliability_index reduces the risk of 
#         stockouts but may come at a higher landed cost.
#     """
#     # 1. Retrieve base cost of item from inventory
#     try:
#         item_res = supabase.table("inventory").select("unit_cost").eq("id", params.item_id).execute()
#     except postgrest.exceptions.APIError as e:
#         return f"ERROR: Invalid UUID format provided ({params.item_id}). Please check the item ID and try again."
#     if not item_res.data:
#         return EvaluateSupplyChainOptionsOutput(options=[])
#     base_cost = float(item_res.data[0]["unit_cost"])
    
#     # 2. Retrieve all suppliers
#     res = supabase.table("suppliers").select("id, avg_lead_time, reliability_score").execute()
#     options = []
#     for s in res.data:
#         # Cost = base cost + logistic surcharge (higher if reliability is low)
#         logistics_surcharge = base_cost * (1.0 - s["reliability_score"]) * settings.LOGISTICS_SURCHARGE_FACTOR
#         total_landed_cost = base_cost + logistics_surcharge
#         options.append(SupplyChainOption(
#             supplier_id=s["id"],
#             total_landed_cost=round(total_landed_cost, 2),
#             reliability_index=s["reliability_score"],
#             estimated_delivery=s["avg_lead_time"]
#         ))
#     return EvaluateSupplyChainOptionsOutput(options=options)

@tool
async def check_operational_capacity(params: CheckOperationalCapacityInput) -> CheckOperationalCapacityOutput:
    """
        Predicts the feasibility of handling a projected surge in orders based on current staff load.
        
        Use this tool before approving promotional campaigns or during festival planning to 
        ensure the kitchen won't reach a breaking point (95% load).
        
        Args:
            params (CheckOperationalCapacityInput):
                - projected_order_surge: Number of extra orders expected.
                - complexity_factor: 1.0 (standard) to 5.0 (labor-intensive prep).
                
        Returns:
            Feasibility status and the number of additional staff members required to 
            bring the projected load back down to the 80% safety threshold.
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
    The primary 'Write' tool for the restaurant system. Executes INTERNAL operational changes only.
    
    Use ONLY for:
    - Permanent menu price updates
    - Inventory adjustments
    - Purchase orders
    - Kitchen alerts
    - Recruitment actions

    Examples:
    - Permanently raise burger price by RM2
    - Adjust inventory stock count
    - Create supplier PO
    - Recruit 2 more staff 

    DO NOT use for temporary promotions, flash sales, coupons, or marketing campaigns.
    Those must use formulate_marketing_strategy.
    
    CRITICAL: This tool requires permission checks. Actions that exceed safety thresholds 
    will be paused for 'Human-in-the-loop' approval via the notifications table.
    
    Args:
        params (ExecuteOperationalActionInput):
            - action_type: 
                'UPDATE_MENU': Change prices or item descriptions.
                'CREATE_PO': Generate a Purchase Order for suppliers.
                'INVENTORY_ADJUST': Manual correction of stock levels.
                'ALERT_KDS': Send a high-priority event to the Kitchen Display System.
                'RECRUIT_STAFF': Recruitement of new staff members.
            - payload: Dictionary containing target_id and the new_value object.
            - logic_summary: Short justification from the Planning/Reasoning agents for the decision log.
            
    Returns:
        Status of 'success', 'failed', or 'pending_approval'. 
        If 'pending_approval', the agent should inform the user that a request has been sent to their dashboard.
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
                    arrival = get_current_simulated_time() + timedelta(hours=sup_res.data[0]["avg_lead_time"])
                    po["arrival_estimate"] = arrival.isoformat()
            supabase.table("procurement_logs").insert(po).execute()
            status = "success"

        elif params.action_type == "INVENTORY_ADJUST":
            supabase.table("inventory").update(params.payload.new_value).eq("id", params.payload.target_id).execute()
            status = "success"

        elif params.action_type == "ALERT_KDS":
            supabase.table("kds_events").insert(params.payload.new_value).execute()
            status = "success"
        
        elif params.action_type == "RECRUIT_STAFF":
            supabase.table("staff_roster").insert(params.payload.new_value).execute()
            status = "success"
        
        if status == "success":
            supabase.table("decision_logs").insert({
                "trigger_signal": params.action_type,
                "timestamp": get_current_simulated_time().isoformat(),
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
        Creates TEMPORARY customer-facing promotional campaigns.

        Use for:
        - Limited-time discounts
        - Flash sales
        - Coupons
        - Bundle promotions
        - Advertising campaigns

        Examples:
        - Friday 20% noodle flash sale
        - Weekend combo voucher
        - Instagram ad boost

        DO NOT use for permanent menu pricing changes.

        Args:
            strategy_type: 'VOUCHER' (direct discount), 'FLASH_SALE' (time-limited), 'AD_BOOST' (visibility).
            goal: 'clear_stock' (prioritize volume) or 'maximize_margin' (prioritize profit).
            config: Includes budget and target audience constraints.

        Returns:
            A unique campaign_id and estimated reach. Note: High-budget campaigns (> RM500) 
            may trigger a human approval requirement in subsequent steps.
    """
    supabase.table("marketing_campaigns").insert({
        "type": params.strategy_type,
        "trigger_event": params.goal,
        "spend": params.config.budget,
        "active_status": True
    }).execute()
    
    return FormulateMarketingStrategyOutput(
        campaign_id=str(uuid.uuid4()),
        activation_timestamp=get_current_simulated_time().isoformat(),
        estimated_reach=int(params.config.budget * 15)
    )

@tool
async def send_human_notification(params: SendHumanNotificationInput) -> SendHumanNotificationOutput:
    """
    Escalates high-stakes or irreversible decisions to a human operator for approval.

    MANDATORY USE CASES:
    - Any expenditure or marketing budget > RM500.
    - Menu price adjustments exceeding 15% of the current price.
    - Major inventory liquidations or high-priority logistics changes.

    Args:
        priority: 'high' for immediate financial/operational risks, 'medium' for routine approvals.
        message: A clear explanation of *why* the action is proposed and the *risk* of inaction.
        proposed_action_json: The exact payload that will be executed upon approval.
        channel: 'dashboard' (default), 'whatsapp', or 'email' for urgent escalations.

    Returns:
        A notification_id used to track the approval status in the 'notifications' table.
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
    Conducts a performance analysis of a completed event and updates the Long-Term Memory (Knowledge Base).

    This tool enables the agent to 'learn' by comparing expected vs. actual outcomes. It uses 
    Z.ai (GLM) embeddings to store the lesson in a vector database for future RAG retrieval.

    Use this after:
    - A marketing campaign ends.
    - A festival/holiday period concludes.
    - A supply chain disruption is resolved.

    Args:
        event_id: The ID of the completed scenario.
        actual_outcome: Realized revenue and waste metrics.
        expected_outcome: (Optional) The initial projection for variance analysis.

    Returns:
        The lesson learned and a similarity score if this event matched a previous scenario 
        (Knowledge Deduplication).
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
    
    if similar.data:

        sim_val = similar.data[0].get("similarity", 0)

        try:
            similarity = float(sim_val)
        except (TypeError, ValueError):
            similarity = 0.0

        if similarity > 0.9:
            best_match = similar.data[0]
            supabase.table("knowledge_base").update({
                "lesson_learned": lesson
            }).eq("id", best_match["id"]).execute()
            return GeneratePostMortemLearningOutput(lesson_learned=lesson, embedding_id=best_match["id"], strategy_adjustment=strategy, similarity_score=best_match["similarity"])

        supabase.table("knowledge_base").insert({
            "embedding_vector": embedding, 
            "scenario_description": lesson, 
            "lesson_learned": strategy, 
            "performance_score": 0.85,
            "created_at": get_current_simulated_time().isoformat()
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
    Fetches external 'Signals' (weather, holidays, logistics news) to provide environmental context.

    Use this tool at the start of a reasoning loop to identify 'Forward-Looking' risks 
    not found in internal databases. This allows the P-Agent to be proactive rather than reactive.

    Example Signals:
    - Monsoon/Weather alerts -> Impacts 'supply_chain_options'.
    - Upcoming Holidays (Mother's Day, Hari Raya) -> Impacts 'operational_capacity'.
    - Price fluctuations in raw materials -> Impacts 'simulate_yield_scenario'.

    Returns:
        A list of articles with an 'impact_level' (low, medium, high) to prioritize reasoning.
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
    
# * Newly added
# ─────────────────────────────────────────────────────────────
# TOOL 1 — get_all_menu_items
# ─────────────────────────────────────────────────────────────
 
@tool
async def get_all_menu_items(params: GetAllMenuItemsInput) -> GetAllMenuItemsOutput:
    """
    For category-specific promotions, ALWAYS set filter_category. Avoid fetching the entire menu unless performing a full audit.Call this before any decision that touches menu items — promotions, price changes,
    ingredient substitutions, or demand forecasting per dish.
 
    When to call:
    - Before simulate_yield_scenario: you need item_id and current_price first
    - Before Constraint-Aware Kitchen Sync: to find substitutable dishes in same category
    - During Profit Preservation: to evaluate which items have margin room for price increases
 
    How to interpret:
    - margin_percent < 20 → flag as margin-vulnerable; protect from discounting
    - is_available=False items → already pulled; do not recommend or promote these
    - ingredients → cross-reference with get_business_state(scope='inventory')
      to check if the dish is at risk from a stock shortage
 
    filter_category: use to narrow results when you only need one section of the menu.
    include_unavailable: set True only during post-mortem or full menu audit.
    """
    query = supabase.table("menu_items").select(
        "id, name, category, current_price, margin_percent, is_available, ingredients"
    )

    if not params.include_unavailable:
        query = query.eq("is_available", True)

    if params.filter_category:
        query = query.ilike("category", params.filter_category)

    res = query.order("category").execute()

    # 2. Map the results
    items = [
        MenuItem(
            item_id=row["id"],
            name=row["name"],
            category=row["category"] or "uncategorised",
            current_price=float(row["current_price"]),
            margin_percent=float(row["margin_percent"]),
            is_available=row["is_available"],
            # Since 'ingredients' is JSONB, Supabase returns it as a Python list of dicts
            ingredients=[
                IngredientDetail(qty=i["qty"], item_name=i["item_name"]) 
                for i in (row.get("ingredients") or [])
            ],
        )
        for row in res.data
    ]

    return GetAllMenuItemsOutput(items=items, total_count=len(items))
 
 
@tool
async def get_menu_pricing_snapshot(
    params: GetMenuPricingSnapshotInput
) -> GetMenuPricingSnapshotOutput:
    """
    Returns a compact pricing snapshot for promotion analysis.

    Use this instead of get_all_menu_items when the request is about:
    - all menu items
    - storewide discounts
    - blanket flash sales
    - full-menu pricing scans

    Output is intentionally compact:
    - item_id
    - name
    - category
    - current_price
    - margin_percent
    - is_available
    """
    query = supabase.table("menu_items").select(
        "id, name, category, current_price, margin_percent, is_available"
    )

    if not params.include_unavailable:
        query = query.eq("is_available", True)

    if params.category_filter:
        query = query.eq("category", params.category_filter)

    res = query.order("category").execute()

    items = [
        MenuItemSnapshot(
            item_id=row["id"],
            name=row["name"],
            category=row["category"] or "uncategorised",
            current_price=float(row["current_price"]),
            margin_percent=float(row["margin_percent"]),
            is_available=bool(row["is_available"]),
        )
        for row in res.data
    ]

    return GetMenuPricingSnapshotOutput(
        items=items,
        total_count=len(items)
    )

# ─────────────────────────────────────────────────────────────
# TOOL 2 — contact_supplier
# ─────────────────────────────────────────────────────────────
import re

def _is_uuid(value: str) -> bool:
    return bool(re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        value or ""
    ))


@tool
async def contact_supplier(params: ContactSupplierInput) -> ContactSupplierOutput:
    """
    Send a structured message to a supplier and log the contact attempt.
    This is the execution step after evaluate_supply_chain_options identifies
    the best supplier — use it to place the actual order or negotiate price.
 
    When to call:
    - Unstructured ingestion detects a price spike → contact alternative supplier for quote
    - Proactive crisis: stock_days < 1 → emergency_restock to primary supplier
    - Demand forecast predicts Friday noodle spike → purchase_order before Thursday EOD
    - Profit preservation mode → price_inquiry to multiple suppliers simultaneously
 
    Message content guidance:
    - Always include: item name, required qty, required delivery date, price ceiling
    - For emergency_restock: open with urgency signal, give a 4-hour delivery window
    - For price_inquiry: include current unit cost so supplier knows your reference point
 
    HARD RULE: Do not call this with message_type='purchase_order' if proposed_qty implies
    spend > RM500 without first getting send_human_notification approved.
 
    channel_used in response:
    - 'logged_only' means no real integration is wired yet — the message is stored in
      supplier_contact_logs for manual follow-up by the operator.
    """
    # Fetch supplier info
    supplier_key = params.supplier_id

    query = supabase.table("suppliers").select(
        "id, name, avg_lead_time, reliability_score, contact_email, contact_phone"
    )

    if _is_uuid(supplier_key):
        supplier_res = query.eq("id", supplier_key).execute()
    else:
        # fallback: search by supplier code or name
        supplier_res = query.or_(
            f"name.ilike.%{supplier_key}%,supplier_code.eq.{supplier_key}"
        ).execute()
 
    if not supplier_res.data:
        return ContactSupplierOutput(
            status="failed",
            contact_log_id="",
            supplier_name="unknown",
            channel_used="logged_only",
            message_preview="Supplier not found.",
            expected_response_hrs=99,
        )
 
    supplier = supplier_res.data[0]
    contact_log_id = f"clog_{uuid.uuid4().hex[:8]}"
 
    # Determine channel — extend this when real integrations are added
    has_email = bool(supplier.get("contact_email"))
    has_phone = bool(supplier.get("contact_phone"))
    channel = "email" if has_email else ("whatsapp" if has_phone else "logged_only")
 
    # Log the contact attempt regardless of channel
    supabase.table("supplier_contact_logs").insert({
        "contact_log_id": contact_log_id,
        "supplier_id": params.supplier_id,
        "supplier_name": supplier["name"],
        "message_type": params.message_type,
        "message_body": params.message_body,
        "proposed_qty": params.proposed_qty,
        "proposed_unit_price": params.proposed_unit_price,
        "channel_used": channel,
        "status": "sent",
    }).execute()
 
    # TODO: plug real send logic here
    # if channel == "email":   await send_email(supplier["contact_email"], params.message_body)
    # if channel == "whatsapp": await send_whatsapp(supplier["contact_phone"], params.message_body)
 
    expected_hrs = int(supplier["avg_lead_time"])
    if params.message_type == "emergency_restock":
        expected_hrs = max(1, expected_hrs // 4)
 
    return ContactSupplierOutput(
        status="sent",
        contact_log_id=contact_log_id,
        supplier_name=supplier["name"],
        channel_used=channel,
        message_preview=params.message_body[:120],
        expected_response_hrs=expected_hrs,
    )
 
 
# ─────────────────────────────────────────────────────────────
# TOOL 3 — save_to_kds
# ─────────────────────────────────────────────────────────────
 
@tool
async def save_to_kds(params: SaveToKdsInput) -> SaveToKdsOutput:
    """
    Push an order or instruction to the Kitchen Display System (KDS).
    This is the final step of Constraint-Aware Kitchen Sync — after the agent rewrites
    the menu or resequences orders, it must push the updated instructions to the kitchen.
 
    When to call:
    - After execute_operational_action(UPDATE_MENU): push the menu change to kitchen screens
    - After a stock depletion forces an ingredient swap: alert kitchen with agent_note
    - After check_operational_capacity detects a surge: resequence with priority='urgent'
      for critical orders and priority='hold' for new incoming ones
 
    priority behaviour:
    - 'normal'  → appended to end of current queue, standard ETA
    - 'urgent'  → inserted at position 1, ETA recalculated for all downstream orders
    - 'hold'    → displayed with a HOLD banner, staff must manually release it
 
    agent_note is shown as a coloured banner on the KDS screen — keep it under 80 chars.
    Good examples:
    - "Swap salmon → sea bass. Stock depleted as of 18:42."
    - "Rice low. Suggest noodle upsell for tables 4-7."
    - "Friday surge expected. Pre-prep noodle base x30."
 
    estimated_prep_minutes should account for current kitchen_load_percent — if load > 80,
    add 50% buffer to your base estimate.
    """
    kds_entry_id = f"kds_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    eta = now + timedelta(minutes=params.estimated_prep_minutes)
 
    # Get current queue length to determine position
    queue_res = supabase.table("kds_queue").select(
        "id", count="exact"
    ).eq("status", "displayed").execute()
    current_queue_length = queue_res.count or 0
 
    position = 1 if params.priority == "urgent" else current_queue_length + 1
 
    supabase.table("kds_queue").insert({
        "kds_entry_id": kds_entry_id,
        "order_id": params.order_id,
        "table_number": params.table_number,
        "items": [item.model_dump() for item in params.items],
        "priority": params.priority,
        "status": "displayed" if params.priority != "hold" else "queued",
        "estimated_prep_minutes": params.estimated_prep_minutes,
        "eta_timestamp": eta.isoformat(),
        "position_in_queue": position,
        "agent_note": params.agent_note,
    }).execute()
 
    # If urgent, shift all other displayed orders down by 1
    if params.priority == "urgent" and current_queue_length > 0:
        existing = supabase.table("kds_queue").select(
            "id, position_in_queue"
        ).eq("status", "displayed").neq("kds_entry_id", kds_entry_id).execute()
 
        for row in existing.data:
            supabase.table("kds_queue").update({
                "position_in_queue": row["position_in_queue"] + 1
            }).eq("id", row["id"]).execute()
 
    return SaveToKdsOutput(
        kds_entry_id=kds_entry_id,
        status="displayed" if params.priority != "hold" else "queued",
        eta_timestamp=eta.isoformat(),
        position_in_queue=position,
    )
 
 
# ─────────────────────────────────────────────────────────────
# TOOL 4 — get_all_orders
# ─────────────────────────────────────────────────────────────
 
@tool
async def get_all_orders(params: GetAllOrdersInput) -> GetAllOrdersOutput:
    """
    Retrieve order history for demand forecasting and post-mortem analysis.
    This is the primary data source for the Demand Forecasting Loop — the agent
    reads recent order patterns to predict tonight's demand per dish.
 
    When to call:
    - Demand Forecasting: fetch last 30 days of completed orders, group by dish + day_of_week
    - Post-mortem: fetch orders from the campaign period to measure actual revenue
    - Proactive crisis: fetch today's pending orders before resequencing in KDS
 
    How to use the output for forecasting:
    - Group orders by day_of_week + hour to find demand patterns
    - Look for Friday/Saturday spikes, Ramadan lunch drops, pre-holiday surges
    - Cross-reference with get_festival_calendar to explain anomalies in history
    - If today matches a historical spike pattern → tighten reorder triggers now
 
    Recommended query patterns:
    - Recent history: date_from=30 days ago, status_filter='completed', limit=500
    - Today's pipeline: status_filter='pending', limit=100
    - Campaign measurement: date_from=campaign_start, date_to=campaign_end
    """
    query = supabase.table("orders").select(
        "id, timestamp, items, total_revenue, total_margin, order_status"
    )
 
    if params.status_filter:
        query = query.eq("order_status", params.status_filter)
 
    if params.date_from:
        query = query.gte("timestamp", params.date_from)
 
    if params.date_to:
        query = query.lte("timestamp", params.date_to)
 
    query = query.order("timestamp", desc=True).limit(params.limit)
    res = query.execute()
 
    orders = [
        OrderRecord(
            order_id=row["id"],
            timestamp=row["timestamp"],
            items=row["items"] or [],
            total_revenue=float(row["total_revenue"]),
            total_margin=float(row["total_margin"]),
            status=row["order_status"],
        )
        for row in res.data
    ]
 
    total_revenue_sum = round(sum(o.total_revenue for o in orders), 2)
 
    return GetAllOrdersOutput(
        orders=orders,
        total_revenue_sum=total_revenue_sum,
        total_count=len(orders),
    )
 
 
# ─────────────────────────────────────────────────────────────
# TOOL 5 — get_festival_calendar
# ─────────────────────────────────────────────────────────────
 
@tool
async def get_festival_calendar(params: GetFestivalCalendarInput) -> GetFestivalCalendarOutput:
    """
    Look up upcoming Malaysian public holidays and major festivals.
    """
    from app.engine.simulator import get_current_simulated_time

    sim_now = get_current_simulated_time()
    today = sim_now.date()
    cutoff = today + timedelta(days=params.days_ahead)

    res = supabase.table("festival_calendar").select("*").gte(
        "event_date", today.isoformat()
    ).lte(
        "event_date", cutoff.isoformat()
    ).order("event_date").execute()

    rows = res.data or []

    # fallback: fetch nearest future event if none in range
    if not rows:
        fallback = supabase.table("festival_calendar").select("*").gte(
            "event_date", today.isoformat()
        ).order("event_date").limit(1).execute()
        rows = fallback.data or []

    events = []
    for row in rows:
        event_date = datetime.fromisoformat(str(row["event_date"])).date()
        days_away = (event_date - today).days
        events.append(FestivalEvent(
            name=row["name"],
            date=row["event_date"],
            days_away=days_away,
            type=row["type"],
            demand_impact=row.get("demand_impact") if params.include_food_impact else None,
            staffing_note=row.get("staffing_note"),
        ))

    nearest = min((e.days_away for e in events), default=999)

    return GetFestivalCalendarOutput(events=events, nearest_event_days_away=nearest)
 
 
# ─────────────────────────────────────────────────────────────
# TOOL 6 — query_macro_context (upgraded — live news)
# ─────────────────────────────────────────────────────────────
 
# Search query map per indicator
_INDICATOR_QUERIES = {
    "oil_price":       "crude oil price Malaysia today",
    "usd_myr":         "USD MYR exchange rate today",
    "local_inflation": "Malaysia inflation CPI latest",
}
 
# Keyword heuristics to derive trend when no numeric value is available
_UP_KEYWORDS    = ["rise", "rises", "rose", "surge", "jump", "spike", "high", "increase", "up"]
_DOWN_KEYWORDS  = ["fall", "falls", "fell", "drop", "decline", "low", "decrease", "down", "ease"]
 
 
async def _fetch_news_headline(query: str) -> tuple[str | None, str | None]:
    """
    Fetch the top news headline for a query.
    Always returns (headline, url), never None.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1",
                },
            )

            data = resp.json()

            abstract = data.get("AbstractText") or data.get("Answer") or ""
            url = data.get("AbstractURL") or data.get("AbstractSource") or ""

            if abstract:
                return abstract[:300], url

            topics = data.get("RelatedTopics", [])
            if topics and isinstance(topics[0], dict):
                text = topics[0].get("Text", "")
                link = topics[0].get("FirstURL", "")
                if text:
                    return text[:300], link

    except Exception as e:
        print(f"Macro news fetch failed for query='{query}': {e}")

    return None, None
 
def _extract_trend(text: str) -> str:
    lower = text.lower()
    up_hits   = sum(1 for w in _UP_KEYWORDS   if w in lower)
    down_hits = sum(1 for w in _DOWN_KEYWORDS if w in lower)
    if up_hits > down_hits:
        return "up"
    elif down_hits > up_hits:
        return "down"
    return "stable"
 
 
def _extract_numeric(text: str, indicator: str) -> float | None:
    """Pull the first plausible numeric value from a headline for a given indicator."""
    import re
    if indicator == "usd_myr":
        m = re.search(r"(\d+\.\d+)\s*(ringgit|MYR|RM)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"USD.*?(\d+\.\d+)", text, re.IGNORECASE)
        return float(m.group(1)) if m else None
    elif indicator == "oil_price":
        m = re.search(r"\$\s?(\d+\.?\d*)\s*(per barrel|barrel|bbl)?", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(\d+\.?\d*)\s*dollars?\s*(per barrel|barrel|bbl)", text, re.IGNORECASE)
        return float(m.group(1)) if m else None
    elif indicator == "local_inflation":
        m = re.search(r"(\d+\.?\d*)\s*%", text)
        return float(m.group(1)) if m else None
    return None
 
 
async def _glm_summarise(headline: str, indicator: str) -> str:
    """Ask GLM to distill a 1-sentence business implication from the headline."""
    try:
        prompt = (
            f"Indicator: {indicator}\n"
            f"Headline: {headline}\n\n"
            "In exactly one sentence, state what this means for a Malaysian restaurant's "
            "food costs, supplier pricing, or customer spending power. Be specific and practical."
        )
        response = await glm_client.chat.completions.create(
            model="glm-4-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return headline[:120]
 
 
@tool
async def query_macro_context(params: QueryMacroContextInput) -> QueryMacroContextOutput:
    """
    Fetch live macro-economic signals from real-world news and derive trend implications.
    This upgraded version replaces the static DB query — it searches for current headlines
    and uses GLM to translate them into actionable restaurant cost signals.
 
    When to call:
    - Before evaluate_supply_chain_options: oil trend affects logistics surcharge multiplier
    - Before contact_supplier with purchase_order: rising r"usd/myr\s*(?:at|to|=)?\s*(\d+\.\d+)" = imported goods more expensive
    - During Profit Preservation crisis mode: get full picture of all three indicators
    - Proactive: schedule daily at market open (09:00 MYT) to refresh agent's cost model
 
    How to use overall_risk_level:
    - 'low'      → normal operations, no macro adjustment needed
    - 'elevated' → apply 10% cost buffer to all supplier POs, flag to operator weekly
    - 'high'     → trigger Profit Preservation Agent immediately, send_human_notification
 
    How to use agent_recommendation:
    - Feed this string directly into the next tool call's reasoning context
    - e.g. if recommendation says "apply 15% logistics surcharge" → pass that to
      evaluate_supply_chain_options so it adjusts total_landed_cost correctly
 
    include_news_summary=True adds GLM-generated 1-sentence business implication per indicator.
    Set False for fast polling loops where you only need the trend signal.
    """
    results: list[MacroIndicatorLive] = []
    high_risk_count = 0
 
    for indicator in params.indicators:
        query_str = _INDICATOR_QUERIES.get(indicator, indicator)
        result  = await _fetch_news_headline(query_str)

        if not result:
            headline, url = None, None
        else:
            headline, url = result
        if headline:    
            trend = _extract_trend(headline)
            value = _extract_numeric(headline, indicator)
            confidence = "medium"
            summary = await _glm_summarise(headline, indicator) if params.include_news_summary else None
        else:
            # Graceful fallback — return stable with low confidence
            trend, value, confidence, summary, url = (
                "unknown",
                None,
                "low",
                "No reliable live macro data retrieved.",
                None
            )
 
        if trend == "up" and indicator in ("oil_price", "local_inflation"):
            high_risk_count += 1
        if trend == "up" and indicator == "usd_myr":
            high_risk_count += 1
 
        results.append(MacroIndicatorLive(
            indicator=indicator,
            value=value,
            trend=trend,
            confidence=confidence,
            news_summary=summary,
            source_url=url,
        ))
 
        unknown_count = sum(1 for r in results if r.trend == "unknown")

        if unknown_count == len(results):
            overall_risk = "unknown"
        elif high_risk_count >= 2:
            overall_risk = "high"
        elif high_risk_count == 1:
            overall_risk = "elevated"
        else:
            overall_risk = "low"
 
    # Build a concrete agent recommendation
    recommendations = []
    for r in results:
        if r.indicator == "oil_price" and r.trend == "up":
            recommendations.append("Apply 15% logistics surcharge to all supplier POs.")
        elif r.indicator == "usd_myr" and r.trend == "up":
            recommendations.append("Favour local suppliers — imported goods cost more in MYR.")
        elif r.indicator == "local_inflation" and r.trend == "up":
            recommendations.append("Consider proactive bulk purchasing before further cost rises.")
 
    agent_recommendation = " ".join(recommendations) if recommendations else (
        "Macro environment stable — no immediate cost adjustments required."
    )
 
    return QueryMacroContextOutput(
        results=results,
        overall_risk_level=overall_risk,
        agent_recommendation=agent_recommendation,
    )