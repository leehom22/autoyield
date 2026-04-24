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

@router.post("/trigger-crisis")
async def trigger_crisis_endpoint(payload: GodModePayload):
    """
    God Mode: apply multipliers to inventory (quantity & unit cost), oil price, and order velocity.
    - If inventory_target_id is provided, affect only that item.
    - Otherwise affect all inventory items.
    - inventory_qty_multiplier and inventory_cost_multiplier are applied separately.
    - If new multipliers are 1.0, fallback to inventory_multiplier (for backward compatibility).
    """
    result = await trigger_crisis(payload)
    return result

# God Mode Crisis Trigger
async def trigger_crisis(payload: GodModePayload):
    # 1. Prioritize new field with updates, else follow the old one
    qty_mult = payload.inventory_qty_multiplier if payload.inventory_qty_multiplier != 1.0 else payload.inventory_multiplier
    cost_mult = payload.inventory_cost_multiplier if payload.inventory_cost_multiplier != 1.0 else payload.inventory_multiplier

    # 2. Inventory Adjustment
    if qty_mult != 1.0 or cost_mult != 1.0:
        if payload.inventory_target_id:
            update_data = {}
            if qty_mult != 1.0:
                update_data["qty"] = supabase.raw(f"qty * {qty_mult}")
            if cost_mult != 1.0:
                update_data["unit_cost"] = supabase.raw(f"unit_cost * {cost_mult}")
            if update_data:
                supabase.table("inventory").update(update_data).eq("id", payload.inventory_target_id).execute()
        else:
            update_data = {}
            if qty_mult != 1.0:
                update_data["qty"] = supabase.raw(f"qty * {qty_mult}")
            if cost_mult != 1.0:
                update_data["unit_cost"] = supabase.raw(f"unit_cost * {cost_mult}")
            if update_data:
                supabase.table("inventory").update(update_data).execute()

    # 3. Oil Price Adjustment
    if payload.oil_price_multiplier != 1.0:
        res = supabase.table("market_trends_history").select("value").eq("indicator", "oil_price").order("recorded_at", desc=True).limit(1).execute()
        if res.data:
            new_oil = res.data[0]["value"] * payload.oil_price_multiplier
            supabase.table("market_trends_history").insert({"indicator": "oil_price", "value": new_oil}).execute()

    # 4. Exchange Rate Adjustment
    if payload.currency_usd_myr != 1.0:
        res = supabase.table("market_trends_history").select("value").eq("indicator", "usd_myr").order("recorded_at", desc=True).limit(1).execute()
        if res.data:
            new_rate = res.data[0]["value"] * payload.currency_usd_myr
        else:
            new_rate = 4.72 * payload.currency_usd_myr
        supabase.table("market_trends_history").insert({"indicator": "usd_myr", "value": new_rate}).execute()

    # 5. Order Velocity Adjustment
    if payload.order_velocity_multiplier != 1.0:
        old_vel = SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
        SYSTEM_STATE["order_velocity_multiplier"] = old_vel * payload.order_velocity_multiplier
        SYSTEM_STATE["order_velocity_multiplier"] = min(10.0, SYSTEM_STATE["order_velocity_multiplier"])

    return {"status": "data_updated"}




# async def trigger_crisis(payload: GodModePayload):
#     # 1. Inventory Adjustment
#     if payload.inventory_multiplier != 1.0:
#         if payload.inventory_target_id:
#             supabase.table("inventory").update({"qty": supabase.raw(f"qty * {payload.inventory_multiplier}")}).eq("id", payload.inventory_target_id).execute()
#         else:
#             supabase.table("inventory").update({"qty": supabase.raw(f"qty * {payload.inventory_multiplier}")}).execute()

#     # 2. Oil Price Adjustment
#     if payload.oil_price_multiplier != 1.0:
#         res = supabase.table("market_trends_history").select("value").eq("indicator", "oil_price").order("recorded_at", desc=True).limit(1).execute()
#         if res.data:
#             new_oil = res.data[0]["value"] * payload.oil_price_multiplier
#             supabase.table("market_trends_history").insert({"indicator": "oil_price", "value": new_oil}).execute()

#     # 3. Order Velocity Adjustment
#     if payload.order_velocity_multiplier != 1.0:
#         old_vel = SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
#         SYSTEM_STATE["order_velocity_multiplier"] = old_vel * payload.order_velocity_multiplier
#         SYSTEM_STATE["order_velocity_multiplier"] = min(10.0, SYSTEM_STATE["order_velocity_multiplier"])

#     return {"status": "data_updated"}