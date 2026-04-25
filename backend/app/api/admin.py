from fastapi import APIRouter, HTTPException, Header
from app.core.supabase import supabase
from app.engine.simulator import world_engine
from datetime import datetime, timezone
import os

router = APIRouter(tags=["Admin"])

ADMIN_SECRET = os.getenv("ADMIN_RESET_SECRET", "autoyield-reset-2026")

@router.post("/full-reset")
async def full_reset(x_admin_secret: str = Header(...)):
    """
    Reset Mechanism:
    1. Call reset_all_data() function in Supabase to reset database
    2. Reset Simulation Time (2026-04-20 08:00 UTC)
    3. Clear order queue in storage
    """
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    # 1. Reset Database
    try:
        result = supabase.rpc("reset_all_data").execute()
        db_message = result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")

    # 2. Reset Simulation Time
    was_paused = world_engine.is_paused
    if not was_paused:
        world_engine.pause_world()

    world_engine.simulated_time = datetime(2026, 4, 20, 8, 0, tzinfo=timezone.utc)
    world_engine.tick_count = 0
    world_engine.active_order_queue.clear()

    if not was_paused:
        world_engine.resume_world()

    return {
        "status": "success",
        "database_reset": db_message,
        "sim_clock_reset": world_engine.simulated_time.isoformat(),
        "message": "Full reset completed (database + simulation clock)."
    }