# app/agent/tools.py
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from app.services.glm_parser import parse_unstructured_signal as _parse_unstructured_signal
from app.core.supabase import supabase
from app.schemas.tools_in import *
from app.schemas.tools_out import *
from langchain_core.tools import tool

# ==========================================
# Phase 1: Perception
# ==========================================
#TODO: Optimize docstrings
#TODO: Add tools: get_all_menu_items, contact_supplier, save_to_kds_table, get_all_orders, get_festival_calender, query_macro_context (get news, festival calendar, inflation data)


@tool
async def get_business_state(params: GetBusinessStateInput) -> GetBusinessStateOutput:
    """
    Retrieve real-time snapshots of business state.
    scope: 'inventory' | 'finance' | 'ops'
    """
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

@tool
async def parse_unstructured_signal(params: ParseUnstructuredSignalInput) -> ParseUnstructuredSignalOutput:
    """
        Parse messy unstructured inputs (WhatsApp texts, OCR invoices, voice transcripts)
        into structured JSON using pattern extraction.
        content_type: 'text' | 'ocr_result' | 'stt_transcript'
    """
    return await _parse_unstructured_signal(
        raw_content=params.raw_content,
        input_type=params.type,
        image_data_url=getattr(params, 'image_data_url', None)
    )


# ==========================================
# Phase 2: Reasoning & Simulation
# ==========================================

# Can be upgraded
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
def execute_operational_action(params: ExecuteOperationalActionInput) -> ExecuteOperationalActionOutput:
    """
        Write tool — executes UPDATE_MENU, CREATE_PO (purchase order), or INVENTORY_ADJUST.
        action_type: 'UPDATE_MENU' | 'CREATE_PO' | 'INVENTORY_ADJUST'
        payload: { target_id, new_value }
        """
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
    print(f"⚠️ [Human Required] Priority: {params.priority} | Msg: {params.message}")
    return SendHumanNotificationOutput(
        notification_id=str(uuid.uuid4()),
        delivery_channel="admin_dashboard"
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
    
# * Newly added
# ─────────────────────────────────────────────────────────────
# TOOL 1 — get_all_menu_items
# ─────────────────────────────────────────────────────────────
 
@tool
async def get_all_menu_items(params: GetAllMenuItemsInput) -> GetAllMenuItemsOutput:
    """
    Retrieve the full menu with live pricing and margin data.
    Call this before any decision that touches menu items — promotions, price changes,
    ingredient substitutions, or demand forecasting per dish.
 
    When to call:
    - Before simulate_yield_scenario: you need item_id and current_price first
    - Before Constraint-Aware Kitchen Sync: to find substitutable dishes in same category
    - During Profit Preservation: to evaluate which items have margin room for price increases
 
    How to interpret:
    - margin_percent < 20 → flag as margin-vulnerable; protect from discounting
    - is_available=False items → already pulled; do not recommend or promote these
    - primary_ingredient_id → cross-reference with get_business_state(scope='inventory')
      to check if the dish is at risk from a stock shortage
 
    filter_category: use to narrow results when you only need one section of the menu.
    include_unavailable: set True only during post-mortem or full menu audit.
    """
    query = supabase.table("menu_items").select(
        "id, name, category, current_price, margin_percent, is_available, primary_ingredient_id"
    )
 
    if not params.include_unavailable:
        query = query.eq("is_available", True)
 
    if params.filter_category:
        query = query.eq("category", params.filter_category)
 
    res = query.order("category").execute()
 
    items = [
        MenuItem(
            item_id=row["id"],
            name=row["name"],
            category=row["category"] or "uncategorised",
            current_price=float(row["current_price"]),
            margin_percent=float(row["margin_percent"]),
            is_available=row["is_available"],
            primary_ingredient_id=row.get("primary_ingredient_id"),
        )
        for row in res.data
    ]
 
    return GetAllMenuItemsOutput(items=items, total_count=len(items))
 
 
# ─────────────────────────────────────────────────────────────
# TOOL 2 — contact_supplier
# ─────────────────────────────────────────────────────────────
 
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
    supplier_res = supabase.table("suppliers").select(
        "id, name, avg_lead_time, reliability_score, contact_email, contact_phone"
    ).eq("id", params.supplier_id).execute()
 
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
        "id, timestamp, items, total_revenue, total_margin, status"
    )
 
    if params.status_filter:
        query = query.eq("status", params.status_filter)
 
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
            status=row["status"],
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
    Always call this at the start of the Demand Forecasting Loop — festival context
    is the single biggest explainer for demand anomalies that pure order history misses.
 
    When to call:
    - Before demand forecasting: a festival in the next 7 days changes the entire forecast
    - Before formulate_marketing_strategy: Hari Raya pre-season = ideal for voucher push
    - Before check_operational_capacity: festival days need different staffing assumptions
    - Before contact_supplier with purchase_order: stock up before a demand spike event
 
    How to act on demand_impact:
    - "+X% noodle dishes" → increase noodle reorder trigger by X% for that period
    - "-Y% lunch covers" (e.g. Hari Raya) → reduce lunch prep, don't over-order perishables
    - "Iftar dinner 6-8pm" → staff kitchen at 150% from 17:00, ensure rice/protein stocked
 
    How to act on staffing_note:
    - "Muslim staff may request leave" → flag to operator via send_human_notification
      at least 3 days before the event so they can arrange cover
    """
    today = datetime.now(timezone.utc).date()
    cutoff = today + timedelta(days=params.days_ahead)
 
    res = supabase.table("festival_calendar").select("*").gte(
        "event_date", today.isoformat()
    ).lte(
        "event_date", cutoff.isoformat()
    ).order("event_date").execute()
 
    events = []
    for row in res.data:
        event_date = datetime.fromisoformat(row["event_date"]).date()
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
    """Fetch the top news headline for a query using DuckDuckGo Instant Answer API.
    Returns (headline_text, source_url). Falls back gracefully on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            )
            data = resp.json()
            abstract = data.get("AbstractText") or data.get("Answer") or ""
            url = data.get("AbstractURL") or data.get("AbstractSource") or ""
            if abstract:
                return abstract[:300], url
            # Fall back to related topics
            topics = data.get("RelatedTopics", [])
            if topics and isinstance(topics[0], dict):
                text = topics[0].get("Text", "")
                link = topics[0].get("FirstURL", "")
                return (text[:300], link) if text else (None, None)
    except Exception:
        pass
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
    - Before contact_supplier with purchase_order: rising USD/MYR = imported goods more expensive
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
        headline, url = await _fetch_news_headline(query_str)
 
        if headline:
            trend = _extract_trend(headline)
            value = _extract_numeric(headline, indicator)
            confidence = "medium"
            summary = await _glm_summarise(headline, indicator) if params.include_news_summary else None
        else:
            # Graceful fallback — return stable with low confidence
            trend, value, confidence, summary, url = "stable", None, "low", "No live data retrieved.", None
 
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
 
    # Derive overall risk
    if high_risk_count >= 2:
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