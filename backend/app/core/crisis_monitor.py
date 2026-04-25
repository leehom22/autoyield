import asyncio
from datetime import datetime
from app.core.supabase import supabase
from app.core.state import SYSTEM_STATE
from app.engine.simulator import get_current_simulated_time
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.engine.simulator import world_engine

# Avoid agent from being triggered when handling crisis
_last_trigger_real_time = {}
_trigger_lock = asyncio.Lock()

async def _can_trigger_and_record(crisis_type: str) -> bool:
    async with _trigger_lock:
        now = get_current_simulated_time()
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

async def _call_agent(app, crisis_msg: str):
    
    graph = app.state.graph
    print(f"🔍 [Crisis Monitor] Processing crisis: {crisis_msg[:100]}...")
    
    # # Pause world
    # world_engine.pause_world()
    # print(f"⏸️ [Crisis Monitor] World paused. Processing crisis: {crisis_msg[:100]}...")
    
    try:
        # Call Agent
        result = await graph.ainvoke({
            "messages": [HumanMessage(content=f"SYSTEM CRISIS DETECTED: {crisis_msg}. Analyze and propose actions.")]
        })
        
        # Record decision log
        supabase.table("decision_logs").insert({
            "trigger_signal": "CRISIS_MONITOR",
            "timestamp": get_current_simulated_time().isoformat(),
            "p_agent_argument": result.get("p_agent_position", ""),
            "r_agent_argument": result.get("r_agent_position", ""),
            "resolution": "Auto-triggered",
            "action_taken": result.get("final_response", "")[:500],
        }).execute()
        print(f"✅ Crisis monitor triggered Agent. Response: {result.get('final_response', '')[:100]}...")
        
    except Exception as e:
        print(f"❌ Crisis monitor failed to call Agent: {e}")
    
    # finally:
    #     # Resume world
    #     world_engine.resume_world()
    #     print("▶️ [Crisis Monitor] World resumed.")


async def check_and_trigger_crisis(app):
    # Don't check data when the world is paused
    if world_engine.is_paused:
        return
    
    current_sim_time = world_engine.simulated_time
    
    # 1. Inventory crisis
    inv_res = supabase.table("inventory").select("id, name, qty, min_stock_level").execute()
    low_stock_items = [i for i in inv_res.data if i["qty"] < i["min_stock_level"]]
    if low_stock_items and await _can_trigger_and_record("inventory_crisis"):
        _record_trigger("inventory_crisis")
        item_names = [i["name"] for i in low_stock_items[:3]]
        msg = f"Inventory crisis: {len(low_stock_items)} items below minimum stock. Examples: {', '.join(item_names)}."
        await _call_agent(app, msg)
        return
    
    # 2. Oil Price Spike (Compare between last 2 price)
    oil_history = supabase.table("market_trends_history").select("value, recorded_at").eq("indicator", "oil_price").order("recorded_at", desc=True).limit(2).execute()
    if len(oil_history.data) >= 2:
        latest = oil_history.data[0]["value"]
        previous = oil_history.data[1]["value"]
        if latest > previous * settings.OIL_PRICE_SPIKE_THRESHOLD and await _can_trigger_and_record("inventory_crisis"):
            _record_trigger("oil_spike")
            pct = (latest / previous - 1) * 100
            msg = f"Oil price spike: from {previous:.2f} to {latest:.2f} (+{pct:.0f}%)."
            await _call_agent(app, msg)
            return
    
    # 3. Abnormal Order Velocity
    velocity = SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
    if velocity > 3.0 and await _can_trigger_and_record("inventory_crisis"):
        _record_trigger("order_surge")
        msg = f"Order velocity surge detected: current multiplier {velocity:.1f}x normal rate."
        await _call_agent(app, msg)
        return

async def crisis_monitor_loop(app):
    while True:
        await check_and_trigger_crisis(app)
        await asyncio.sleep(5)  # Check every 5 seconds