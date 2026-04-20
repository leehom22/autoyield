from fastapi import APIRouter, Request, BackgroundTasks
from langchain_core.messages import HumanMessage

router = APIRouter()

# Trigger Agent when Low Stock
async def trigger_crisis_debate(app, item_id: str):
    graph = app.state.graph
    await graph.ainvoke({
        "messages": [HumanMessage(content=f"SYSTEM ALERT: Stock Critical for item_id={item_id}. Initiate Proactive Response and margin evaluation.")]
    })

# Proactive Triggering: Listen to Supabase Webhook for inventory updates.
@router.post("/inventory")
async def handle_inventory_depletion(request: Request, background_tasks: BackgroundTasks):
    
    payload = await request.json()
    
    # Parsing JSON structure from Supabase Webhook (old_record, record)
    record = payload.get("record", {})
    item_id = record.get("id")
    current_qty = record.get("qty")
    min_stock = record.get("min_stock_level")
    
    # Check threshold
    if current_qty is not None and min_stock is not None:
        if current_qty < min_stock:
            print(f"⚠️ [Sense] Breach detected for item {item_id}. Waking up Agent Kernel.")
            background_tasks.add_task(trigger_crisis_debate, request.app, item_id)
            
    return {"status": "sensed"}