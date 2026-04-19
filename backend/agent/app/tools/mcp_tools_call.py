
from langchain_core.tools import StructuredTool
from app.tools.mcp_client import MCPClient

mcp_client = MCPClient(server_url="http://localhost:8000")

def get_all_lc_tools(mcp_client: MCPClient):
    return [
         StructuredTool.from_function(
            func=mcp_client.get_business_state,
            name= "get_business_state",
            description= "Retrieve real-time snapshots of business state.",
        ),
         StructuredTool.from_function(
            func=mcp_client.parse_unstructured_signal,
            name= "parse_unstructured_signal",
            description= "Parse messy unstructured inputs (WhatsApp texts, OCR invoices, voice transcripts) into structured JSON using pattern extraction.",
        ),
         StructuredTool.from_function(
            func=mcp_client.query_macro_context,
            name= "query_macro_context",
            description= "Fetch macro-economic indicators to adjust risk and logistics weights.",
        ),
         StructuredTool.from_function(
            func=mcp_client.simulate_yield_scenario,
            name= "simulate_yield_scenario",
            description= "Simulate the profit impact of a price change or bundle deal.",
        ),
         StructuredTool.from_function(
            func=mcp_client.evaluate_supply_chain_options,
            name= "evaluate_supply_chain_options",
            description= "Compare all suppliers for a given inventory item by total landed cost vs reliability.",
        ),
         StructuredTool.from_function(
            func=mcp_client.check_operational_capacity,
            name= "check_operational_capacity",
            description= "Validate if current staff can handle a projected order surge.",
        ),
         StructuredTool.from_function(
            func=mcp_client.execute_operational_action,
            name= "execute_operational_action",
            description= "Write tool — executes UPDATE_MENU, CREATE_PO (purchase order), or INVENTORY_ADJUST.",
        ),
         StructuredTool.from_function(
            func=mcp_client.formulate_marketing_strategy,
            name= "formulate_marketing_strategy",
            description= "Trigger a targeted marketing campaign.",
        ),
         StructuredTool.from_function(
            func=mcp_client.send_human_notification,
            name= "send_human_notification",
            description= "Send an Approve/Reject notification to the human operator for high-stakes decisions (spending > RM500, price changes > 15%).",
        ),
         StructuredTool.from_function(
            func=mcp_client.generate_post_mortem_learning,
            name= "generate_post_mortem_learning",
            description= "Compare expected vs actual outcome, write a lesson into the knowledge base.",
        ),
    ]
    

