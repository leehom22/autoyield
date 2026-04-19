from fastapi import APIRouter
from app.schemas.payloads import GodModeVelocityPayload, GodModePayload
from app.core.state import SYSTEM_STATE

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
async def trigger_crisis(payload: GodModePayload):

    # TODO: 使用 supabase-py 客户端更新 market_trends 和 inventory 表
    # 如果 payload.inventory_multiplier != 1.0: 批量更新库存
    # 如果 payload.oil_price_multiplier != 1.0: 更新 market_trends
    
    return {"status": "crisis_injected", "payload": payload.dict()}