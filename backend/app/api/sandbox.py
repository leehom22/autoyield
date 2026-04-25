from fastapi import APIRouter, BackgroundTasks, Request
from app.schemas.payloads import GodModeVelocityPayload, GodModePayload
from app.core.state import SYSTEM_STATE
from app.core.supabase import supabase


router = APIRouter()


# ============== Simulation Controller ==============

@router.post("/pause")
async def pause_simulation():
    from app.engine.simulator import world_engine
    world_engine.pause_world()
    return {"status": "paused", "message": "Simulation time stopped."}

@router.post("/resume")
async def resume_simulation():
    from app.engine.simulator import world_engine
    world_engine.resume_world()
    return {"status": "resumed", "message": "Simulation time resumed."}

@router.get("/status")
async def simulation_status():
    from app.engine.simulator import world_engine
    return {
        "is_paused": world_engine.is_paused,
        "simulated_time": world_engine.simulated_time.isoformat(),
        "velocity": world_engine.velocity if hasattr(world_engine, 'velocity') else SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
    }




# ========== GOD MODE Endpoints (Frontend Slider) ===========

# Adjust order generation velocity
@router.post("/adjust-velocity")
async def adjust_velocity(payload: GodModeVelocityPayload):
    
    old_v = SYSTEM_STATE["order_velocity_multiplier"]
    SYSTEM_STATE["order_velocity_multiplier"] = payload.order_velocity_multiplier
    
    return {
        "status": "success", 
        "trace": f"Velocity shifted: {old_v}x -> {payload.order_velocity_multiplier}x"
    }


# God Mode Crisis Trigger
@router.post("/trigger-crisis")
async def trigger_crisis_endpoint(payload: GodModePayload):
    return await trigger_crisis(payload)

async def trigger_crisis(payload: GodModePayload):
    # New fields
    qty_mult = payload.inventory_qty_multiplier if payload.inventory_qty_multiplier != 1.0 else payload.inventory_multiplier
    cost_mult = payload.inventory_cost_multiplier if payload.inventory_cost_multiplier != 1.0 else payload.inventory_multiplier

    # 1. Inventory Adjustment
    if qty_mult != 1.0 or cost_mult != 1.0:
        if payload.inventory_target_id:
            result = supabase.table("inventory").select("qty, unit_cost").eq("id", payload.inventory_target_id).execute()
            if result.data:
                item = result.data[0]
                updates = {}
                if qty_mult != 1.0:
                    updates["qty"] = item["qty"] * qty_mult
                if cost_mult != 1.0:
                    updates["unit_cost"] = item["unit_cost"] * cost_mult
                if updates:
                    supabase.table("inventory").update(updates).eq("id", payload.inventory_target_id).execute()
        else:
            items = supabase.table("inventory").select("id, qty, unit_cost").execute()
            for item in items.data:
                updates = {}
                if qty_mult != 1.0:
                    updates["qty"] = item["qty"] * qty_mult
                if cost_mult != 1.0:
                    updates["unit_cost"] = item["unit_cost"] * cost_mult
                if updates:
                    supabase.table("inventory").update(updates).eq("id", item["id"]).execute()

    # 2. Oil Price Adjustment
    if payload.oil_price_multiplier != 1.0:
        res = supabase.table("market_trends_history").select("value").eq("indicator", "oil_price").order("recorded_at", desc=True).limit(1).execute()
        if res.data:
            new_oil = res.data[0]["value"] * payload.oil_price_multiplier
            supabase.table("market_trends_history").insert({"indicator": "oil_price", "value": new_oil}).execute()

    # 3. Order Velocity Adjustment
    if payload.order_velocity_multiplier != 1.0:
        old_vel = SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
        SYSTEM_STATE["order_velocity_multiplier"] = old_vel * payload.order_velocity_multiplier
        SYSTEM_STATE["order_velocity_multiplier"] = min(10.0, SYSTEM_STATE["order_velocity_multiplier"])

    return {"status": "data_updated"}