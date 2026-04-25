import asyncio
from datetime import datetime
from app.core.supabase import supabase
from app.core.state import SYSTEM_STATE
from app.engine.simulator import get_current_simulated_time
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.graph.proactive_graph import get_proactive_graph
from app.graph.forecast_graph import get_forecast_graph
from app.engine.simulator import world_engine

# Avoid agent from being triggered when handling crisis
_last_trigger_real_time = {}
_trigger_lock = asyncio.Lock()

async def _can_trigger_and_record(crisis_type: str) -> bool:
    async with _trigger_lock:
        now = datetime.now()
        last = _last_trigger_real_time.get(crisis_type)
        if last is None:
            _last_trigger_real_time[crisis_type] = now
            return True
        elapsed = (now - last).total_seconds()
        if elapsed >= settings.CRISIS_COOLDOWN_SECONDS:
            _last_trigger_real_time[crisis_type] = now
            return True
        return False

def _record_trigger(crisis_type: str):
    _last_trigger_real_time[crisis_type] = datetime.now()

async def _call_proactive_agent(app, crisis_msg: str):
    graph = get_proactive_graph()
    print(f"🔍 [Crisis Monitor] Routing to proactive_graph: {crisis_msg[:100]}...")

    try:
        result = await graph.ainvoke({
            "messages": [
                HumanMessage(
                    content=f"SYSTEM CRISIS DETECTED: {crisis_msg}. Analyze and propose actions."
                )
            ],

            "direct_route": "crisis_optimizer",
            "crisis_message": crisis_msg,

            "anomaly_type": "unknown",
            "pending_handler": "crisis_optimizer",

            "margin_summary": "",
            "capacity_summary": "",
            "menu_rewrite_summary": "",
            "kds_summary": "",
            "final_response": "",

            "action_taken": False,
            "node_tool_call_count": 0,
        })

        supabase.table("decision_logs").insert({
            "trigger_signal": "CRISIS_MONITOR_PROACTIVE",
            "timestamp": get_current_simulated_time().isoformat(),
            "p_agent_argument": "",
            "r_agent_argument": "",
            "resolution": "Auto-triggered proactive crisis response",
            "action_taken": result.get("final_response", "")[:500],
        }).execute()

        print(f"✅ Proactive agent completed: {result.get('final_response', '')[:100]}...")

    except Exception as e:
        print(f"❌ Proactive agent failed: {e}")


async def _call_forecast_agent(app, crisis_msg: str):
    graph = get_forecast_graph()
    print(f"🔍 [Crisis Monitor] Routing to forecast_graph crisis_optimizer: {crisis_msg[:100]}...")

    try:
        result = await graph.ainvoke({
            "messages": [
                HumanMessage(
                    content=f"MACRO CRISIS DETECTED: {crisis_msg}. Analyze macro impact and propose forecast-based actions."
                )
            ],

            "forecast_path": "crisis",
            "user_query": crisis_msg,
            "signal_summary": crisis_msg,

            "reorder_plan": "",
            "kitchen_warning": "",
            "constraint_summary": "",
            "revised_plan": "",
            "forecast_result": "",

            "macro_risk_level": "high",
            "plan_generated": False,

            "pending_handler": "crisis_optimizer",
            "notification_sent": False,
            "notification_id": "",
            "node_tool_call_count": 0,
        })

        supabase.table("decision_logs").insert({
            "trigger_signal": "CRISIS_MONITOR_FORECAST",
            "timestamp": get_current_simulated_time().isoformat(),
            "p_agent_argument": "",
            "r_agent_argument": "",
            "resolution": "Auto-triggered macro forecast crisis response",
            "action_taken": result.get("forecast_result", "")[:500],
        }).execute()

        print(f"✅ Forecast agent completed: {result.get('forecast_result', '')[:100]}...")

    except Exception as e:
        print(f"❌ Forecast agent failed: {e}")


async def check_and_trigger_crisis(app):
    # Ship checking if the world paused
    if world_engine.is_paused:
        return
    
    proactive_msgs = []
    forecast_msgs = []
    
    # 1. Inventory crisis (Proactive)
    inv_res = supabase.table("inventory").select("id, name, qty, min_stock_level").execute()
    low_stock_items = [i for i in inv_res.data if i["qty"] < i["min_stock_level"]]
    if low_stock_items and await _can_trigger_and_record("inventory_crisis"):
        _record_trigger("inventory_crisis")
        item_names = [i["name"] for i in low_stock_items[:3]]
        proactive_msgs.append(f"Inventory crisis: {len(low_stock_items)} items below minimum stock. Examples: {', '.join(item_names)}.")
    
    # 2. Oil Price Spike (Forecast)
    oil_history = supabase.table("market_trends_history").select("value, recorded_at").eq("indicator", "oil_price").order("recorded_at", desc=True).limit(2).execute()
    if len(oil_history.data) >= 2:
        latest = oil_history.data[0]["value"]
        previous = oil_history.data[1]["value"]
        if latest > previous * settings.OIL_PRICE_SPIKE_THRESHOLD and await _can_trigger_and_record("oil_spike"):
            _record_trigger("oil_spike")
            pct = (latest / previous - 1) * 100
            forecast_msgs.append(f"Oil price spike: from {previous:.2f} to {latest:.2f} (+{pct:.0f}%).")
    
    # 3. Abnormal Order Velocity (Proactive)
    velocity = SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
    if velocity > 3.0 and await _can_trigger_and_record("order_surge"):
        _record_trigger("order_surge")
        proactive_msgs.append(f"Order velocity surge detected: current multiplier {velocity:.1f}x normal rate.")

    # Return if no crisis
    if not proactive_msgs and not forecast_msgs:
        return

    # Freeze the time for solving crisis
    world_engine.pause_world()
    try:
        if proactive_msgs:
            combined_proactive = " | ".join(proactive_msgs)
            await _call_proactive_agent(app, combined_proactive)
            
        if forecast_msgs:
            combined_forecast = " | ".join(forecast_msgs)
            await _call_forecast_agent(app, combined_forecast)
    finally:
        world_engine.resume_world()

async def crisis_monitor_loop(app):
    while True:
        await check_and_trigger_crisis(app)
        await asyncio.sleep(2)   # Check every 2s