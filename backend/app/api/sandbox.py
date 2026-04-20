from fastapi import APIRouter, BackgroundTasks
from app.schemas.payloads import GodModeVelocityPayload, GodModePayload
from app.core.state import SYSTEM_STATE
from app.core.supabase import supabase
from backend.main import app
from langchain_core.messages import HumanMessage


router = APIRouter()

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
async def trigger_crisis(payload: GodModePayload):
    
    # 1. Update inventory based on changing multiplier
    if payload.inventory_multiplier != 1.0:
        if payload.inventory_target_id:
            # Update specific item
            supabase.table("inventory").update({"qty": supabase.raw(f"qty * {payload.inventory_multiplier}")}).eq("id", payload.inventory_target_id).execute()
        else:
            # Update all items as a whole
            supabase.table("inventory").update({"qty": supabase.raw(f"qty * {payload.inventory_multiplier}")}).execute()
    
    # 2. Update market trend if multiplier provided
    if payload.oil_price_multiplier != 1.0:
        res = supabase.table("market_trends_history").select("value").eq("indicator", "oil_price").order("recorded_at", desc=True).limit(1).execute()
        if res.data:
            new_oil = res.data[0]["value"] * payload.oil_price_multiplier
            supabase.table("market_trends_history").insert({"indicator": "oil_price", "value": new_oil}).execute()
    
    # 3. Call P/R Agent Graph for debate
    graph = app.state.graph
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=f"God Mode crisis: oil price multiplier {payload.oil_price_multiplier}, inventory multiplier {payload.inventory_multiplier}. Analyze impact and propose actions.")]
    })
    final_response = result.get("final_response", "")
    
    # Record debate outcome in DB decision logs
    supabase.table("decision_logs").insert({
        "trigger_signal": "GOD_MODE_CRISIS",
        "p_agent_argument": result.get("p_agent_position", ""),
        "r_agent_argument": result.get("r_agent_position", ""),
        "resolution": "Debate completed",
        "action_taken": final_response[:500],
    }).execute()
    
    return {"status": "crisis_injected", "response": final_response}