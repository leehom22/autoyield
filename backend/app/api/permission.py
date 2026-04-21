from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.core.supabase import supabase
from app.services.permission_service import invalidate_cache

router = APIRouter()

class PermissionUpdate(BaseModel):
    allow_auto_price_update: Optional[bool] = None
    allow_auto_po_creation: Optional[bool] = None
    allow_auto_inventory_adjust: Optional[bool] = None
    allow_auto_marketing_campaign: Optional[bool] = None
    max_price_change_percent: Optional[float] = None
    max_spend_amount: Optional[float] = None
    max_discount_percent: Optional[float] = None
    approval_mode_for_price_change: Optional[str] = None
    approval_mode_for_po: Optional[str] = None
    approval_mode_for_campaign: Optional[str] = None

@router.get("/")
async def get_permissions():
    res = supabase.table("agent_permissions").select("*").limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Permission config not found")
    return res.data[0]

@router.put("/")
async def update_permissions(updates: PermissionUpdate):
    # Retrieve current id
    res = supabase.table("agent_permissions").select("id").limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Permission config not found")
    record_id = res.data[0]["id"]

    update_data = updates.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        supabase.table("agent_permissions").update(update_data).eq("id", record_id).execute()
        invalidate_cache()  # Clear cache

    return {"status": "success"}