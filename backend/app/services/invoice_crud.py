from typing import Dict, Any, List
from app.core.supabase import supabase
from app.services.db_service import get_inventory_status

async def execute_invoice_crud(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create purchase orders and update inventory based on extracted invoice data.
    
    Args:
        invoice_data: Dictionary from extract_invoice_data
    
    Returns:
        Dict with status, purchase_order_ids, items_processed
    """
    supplier_name = invoice_data.get("supplier")
    items = invoice_data.get("items", [])
    created_pos = []
    items_processed = 0
    
    # Get or create supplier ID
    supplier_id = await get_or_create_supplier(supplier_name)
    
    # Get current inventory (to find item IDs)
    inv_items = get_inventory_status()
    
    for item in items:
        item_name = item.get("name")
        qty = item.get("quantity")
        unit_cost = item.get("unit_price")
        
        if not item_name or qty is None or unit_cost is None:
            continue
        
        # Find matching inventory item (case-insensitive)
        inv_item = next(
            (i for i in inv_items if i["name"].lower() == item_name.lower()),
            None
        )
        if not inv_item:
            # If item not found, you could optionally create it, but for now skip
            print(f"Invoice item '{item_name}' not found in inventory, skipping")
            continue
        
        item_id = inv_item["id"]
        
        # Insert into procurement_logs
        po_record = {
            "item_id": item_id,
            "supplier_id": supplier_id,
            "qty": qty,
            "unit_cost": unit_cost,
            "delivery_status": "ordered",
            "arrival_estimate": None  # Could be calculated from avg_lead_time
        }
        result = supabase.table("procurement_logs").insert(po_record).execute()
        if result.data:
            created_pos.append(result.data[0]["id"])
            items_processed += 1
        
        # Update inventory quantity (add received stock)
        current_qty = inv_item["qty"]
        new_qty = current_qty + qty
        supabase.table("inventory").update({"qty": new_qty}).eq("id", item_id).execute()
    
    return {
        "status": "success" if items_processed > 0 else "no_items_processed",
        "purchase_order_ids": created_pos,
        "items_processed": items_processed
    }


async def get_or_create_supplier(name: str) -> str:
    """Get supplier ID by name, or create a new supplier if not exists."""
    if not name:
        # Return a default supplier ID (you should create one in DB)
        # For now, try to find any supplier or use a placeholder
        res = supabase.table("suppliers").select("id").limit(1).execute()
        if res.data:
            return res.data[0]["id"]
        else:
            # Create a default supplier
            new = {
                "name": "Unknown Supplier",
                "categories": [],
                "reliability_score": 0.5,
                "avg_lead_time": 24,
                "min_order_qty": 0,
                "pricing_tiers": {}
            }
            result = supabase.table("suppliers").insert(new).execute()
            return result.data[0]["id"]
    
    # Try to find existing supplier
    res = supabase.table("suppliers").select("id").eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    
    # Create new supplier
    new_supplier = {
        "name": name,
        "categories": [],
        "reliability_score": 0.7,  # Default moderate reliability
        "avg_lead_time": 48,
        "min_order_qty": 0,
        "pricing_tiers": {}
    }
    result = supabase.table("suppliers").insert(new_supplier).execute()
    return result.data[0]["id"]