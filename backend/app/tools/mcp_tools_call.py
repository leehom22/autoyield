from langchain_core.tools import StructuredTool
from app.tools.tools import *


def get_all_lc_tools() -> list:
    return [get_business_state, 
            query_macro_context,
            # parse_unstructured_signal,
            fetch_macro_news,
            simulate_yield_scenario,
            evaluate_supply_chain_options,
            check_operational_capacity,
            execute_operational_action,
            formulate_marketing_strategy,
            send_human_notification,
            generate_post_mortem_learning
            ]
    

