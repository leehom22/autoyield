from fastapi import APIRouter, BackgroundTasks
from app.schemas.payloads import GodModeVelocityPayload, GodModePayload
from app.core.state import SYSTEM_STATE
from app.graph.main_graph import get_main_graph


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

# Market Crisis (Inventory shock or Oil Price Surge)
@router.post("/trigger-crisis")
async def trigger_crisis(payload: GodModePayload, background_tasks: BackgroundTasks):

    main_graph = get_main_graph()

    # TODO: 使用 supabase-py 客户端更新 market_trends 和 inventory 表
    # 如果 payload.inventory_multiplier != 1.0: 批量更新库存
    # 如果 payload.oil_price_multiplier != 1.0: 更新 market_trends

    initial_state = {
        "raw_content": f"Oil price changed by {payload.oil_price_multiplier}x, inventory multiplier {payload.inventory_multiplier}x. Analyze impact and propose actions.",
        "input_type": "text",
        "image_data_url": None,
        "source": "god_mode",
        "parsed_intent": "GENERAL_CRISIS",
        "parsed_entities": {},
        "parsed_autonomy": "L3",
        "is_complete": True,
        "missing_fields": [],
        "target_agent": None,
        "invoice_data": None,
        "price_spike_detected": False,
        "clerk_result": None,
        "analysis_result": None,
        "debate_context": {"trigger": "GOD_MODE_CRISIS"},
        "debate_result": None,
        "execution_result": None,
        "final_response": "",
        "messages": [],
    }
    
    background_tasks.add_task(main_graph.ainvoke, initial_state)
    
    return {"status": "crisis_injected", "payload": payload.dict()}