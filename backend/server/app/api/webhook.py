# app/api/webhooks/triggers.py
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

@router.post("/inventory")
async def handle_inventory_depletion(request: Request, background_tasks: BackgroundTasks):
    """
    Proactive Triggering: Listen to Supabase Webhook for inventory updates.
    """
    payload = await request.json()
    
    # Parsing JSON structure from Supabase Webhook (old_record, record)
    record = payload.get("record", {})
    item_id = record.get("id")
    current_qty = record.get("qty")
    min_stock = record.get("min_stock_level")
    
    # 核心判断逻辑：是否击穿阈值
    if current_qty is not None and min_stock is not None:
        if current_qty < min_stock:
            print(f"⚠️ [Sense] Breach detected for item {item_id}. Waking up Agent Kernel.")
            
            # 【关键防御】：必须作为后台任务唤醒，否则阻断 Supabase 的 Webhook 导致重试风暴
            # background_tasks.add_task(kernel.run_crisis_debate, item_id=item_id, trigger="inventory_shortage")
            
    return {"status": "sensed"}