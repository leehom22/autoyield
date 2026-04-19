from app.core.supabase import supabase
from typing import List, Dict, Any

# ==========================================
# 1. Menu Operations (Agent 动作核心)
# ==========================================
def get_active_menu() -> List[Dict[str, Any]]:
    """获取当前活跃菜单（包含 JSONB 的配方）"""
    res = supabase.table("menu_items").select("*").eq("status", "active").execute()
    return res.data

def update_menu_item(item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Agent 调价或隐藏菜品时调用"""
    res = supabase.table("menu_items").update(updates).eq("id", item_id).execute()
    return res.data[0] if res.data else {}

# ==========================================
# 2. Order Operations (模拟引擎流动核心)
# ==========================================
def insert_mock_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """引擎生成订单时插入"""
    res = supabase.table("orders").insert(order_data).execute()
    return res.data[0] if res.data else {}

def get_recent_orders(limit: int = 20) -> List[Dict[str, Any]]:
    """获取最近订单，供前端展示或 Agent 分析"""
    res = supabase.table("orders").select("*").order("timestamp", desc=True).limit(limit).execute()
    return res.data

# ==========================================
# 3. Supplier Operations (Agent 供应链推理核心)
# ==========================================
def get_all_suppliers() -> List[Dict[str, Any]]:
    """获取所有供应商及其可靠性分数和阶梯定价"""
    res = supabase.table("suppliers").select("*").execute()
    return res.data

def get_inventory_status() -> List[Dict[str, Any]]:
    """获取库存现状，用于感知层"""
    res = supabase.table("inventory").select("*").execute()
    return res.data