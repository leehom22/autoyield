from app.core.supabase import supabase
from typing import List, Dict, Any, Optional

# ==========================================
# 1. Menu Operations
# ==========================================
def get_active_menu() -> List[Dict[str, Any]]:
    res = supabase.table("menu_items").select("*").eq("status", "active").execute()
    return res.data

def update_menu_item(item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("menu_items").update(updates).eq("id", item_id).execute()
    return res.data[0] if res.data else {}

# ==========================================
# 2. Order Operations
# ==========================================
def insert_mock_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("orders").insert(order_data).execute()
    return res.data[0] if res.data else {}

def get_recent_orders(limit: int = 20) -> List[Dict[str, Any]]:
    res = supabase.table("orders").select("*").order("timestamp", desc=True).limit(limit).execute()
    return res.data

# ==========================================
# 3. Supplier Operations
# ==========================================
def get_all_suppliers() -> List[Dict[str, Any]]:
    res = supabase.table("suppliers").select("*").execute()
    return res.data

def get_inventory_status() -> List[Dict[str, Any]]:
    res = supabase.table("inventory").select("*").execute()
    return res.data


# ==========================================
# 4. Inventory Operations
# ==========================================
def get_inventory_item(name: str) -> Optional[Dict[str, Any]]:
    # Not case-sensitive
    res = supabase.table("inventory").select("*").ilike("name", name).limit(1).execute()
    return res.data[0] if res.data else None

def update_inventory_quantity(item_id: str, new_qty: float) -> Dict[str, Any]:
    res = supabase.table("inventory").update({"qty": new_qty}).eq("id", item_id).execute()
    return res.data[0] if res.data else {}