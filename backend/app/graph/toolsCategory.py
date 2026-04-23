
from app.tools.mcp_tools_call import *

PLANNING_TOOLS = [
    get_business_state,
    get_all_menu_items,
    simulate_yield_scenario,
    check_operational_capacity,
    get_all_orders,
    get_menu_pricing_snapshot,
    get_festival_calendar
]

EXECUTION_TOOLS = [
    execute_operational_action,
    contact_supplier,
    save_to_kds,
    formulate_marketing_strategy,
    send_human_notification,
    generate_post_mortem_learning
]

LEARNING_TOOLS = [
    generate_post_mortem_learning
]