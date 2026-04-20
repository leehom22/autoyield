from cachetools import TTLCache
from app.core.supabase import supabase

# 10s cache to prevent frequent supabase querying
_config_cache = TTLCache(maxsize=1, ttl=10)

def _get_config():
    if "config" in _config_cache:
        return _config_cache["config"]
    res = supabase.table("agent_permissions").select("*").limit(1).execute()
    if not res.data:
        # Default value
        default = {
            "allow_auto_price_update": True,
            "allow_auto_po_creation": True,
            "allow_auto_inventory_adjust": True,
            "allow_auto_marketing_campaign": False,
            "max_price_change_percent": 15.0,
            "max_spend_amount": 500.0,
            "max_discount_percent": 30.0,
            "approval_mode_for_price_change": "require_approval",
            "approval_mode_for_po": "require_approval",
            "approval_mode_for_campaign": "require_approval",
        }
        _config_cache["config"] = default
        return default
    _config_cache["config"] = res.data[0]
    return res.data[0]

# ======== To be call as a part of the prompt of Agent =========
def get_permission_context_for_prompt() -> str:
    cfg = _get_config()
    return f"""
[OPERATIONAL BOUNDARIES - ENFORCED BY SYSTEM]
- Maximum spend without approval: RM{cfg.get('max_spend_amount', 500)}
- Auto price update: {'ENABLED' if cfg.get('allow_auto_price_update') else 'DISABLED'}
- Maximum price change / discount: {cfg.get('max_price_change_percent', 15)}%
Do NOT propose actions that violate these limits unless you explicitly plan to request human approval.
"""

def check_action_permission(action_type: str, payload: dict) -> tuple[bool, str]:
    """
    Return (allowed, reason)
    reason maybe "Approval required: ..." or "Auto-rejected: ..."
    """
    cfg = _get_config()

    if action_type == "CREATE_PO":
        # Caclculate the total value involved in invoice
        new_val = payload.get("new_value", {})
        qty = new_val.get("qty", 0)
        unit_cost = new_val.get("unit_cost", 0)
        total = float(qty) * float(unit_cost)
        max_spend = float(cfg.get("max_spend_amount", 500))
        if total > max_spend:
            mode = cfg.get("approval_mode_for_po", "require_approval")
            if mode == "auto_reject":
                return False, f"Auto-rejected: PO total RM{total:.2f} exceeds strict limit RM{max_spend:.2f}."
            return False, f"Approval required: PO total RM{total:.2f} exceeds auto-limit RM{max_spend:.2f}."
        if not cfg.get("allow_auto_po_creation"):
            return False, "Approval required: Auto PO creation is globally disabled."

    elif action_type == "UPDATE_MENU":
        if not cfg.get("allow_auto_price_update"):
            return False, "Approval required: Auto price update is globally disabled."

    elif action_type == "INVENTORY_ADJUST":
        if not cfg.get("allow_auto_inventory_adjust"):
            return False, "Approval required: Auto inventory adjust is globally disabled."

    # Can be scaled to additional action_type
    return True, "Allowed"

# Clear cache after the API called
def invalidate_cache():
    _config_cache.clear()