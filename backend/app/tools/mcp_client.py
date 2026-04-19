"""
tools/mcp_server.py — FastMCP server exposing all 9 agent tools
Run standalone: python -m tools.mcp_server
"""
import json
import uuid
from datetime import datetime
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from db.client import get_supabase
from typing import Dict

mcp = FastMCP(
    name="mex-agent-tools",
    instructions="Tools for the MEX restaurant AI agent. Use these to perceive business state, reason about decisions, execute actions, and log learnings."
)

class MCPClient:
    """Client to call MCP tools from the LangGraph agent."""
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.timeout = 30.0
        self._session: ClientSession = None

    @asynccontextmanager
    async def connect(self):
        """Establish a session with the MCP server."""
        url = f"{self.server_url}/mcp/sse"
        print(f"=== Connecting to MCP Server via SSE at {url} ===")
        
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session 
                print("✅ MCP Session initialized")
                try:
                    yield session
                finally:
                    self._session = None
                    print("MCP Session closed.")

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the persistent MCP session."""
        try:
            if self._session is None:
                raise RuntimeError("MCP session not connected. Call await mcp_client.connect() first.")

            print(f"\n{'='*60}")
            print(f"🔵 AGENT → MCP | Tool: {tool_name}")
            print(f"   Parameters: {json.dumps(parameters, indent=2)}")

            result = await self._session.call_tool(tool_name, parameters)

            print(f"🟢 MCP → AGENT | Result: {result.content}")
            print(f"{'='*60}\n")

            return {"result": result.content, "success": True}

        except Exception as e:
            print(f"❌ Error calling tool '{tool_name}': {e}")
            return {"result": str(e), "success": False}
  
            
    # ─────────────────────────────────────────────
    # PHASE 1 — PERCEPTION
    # ─────────────────────────────────────────────

    async def get_business_state(self,scope: str) -> Dict[str,Any]:
        """
        Retrieve real-time snapshots of business state.
        scope: 'inventory' | 'finance' | 'ops'
        """
        return await self.call_tool("get_business_state",{
            "scope": scope
        }) 

    async def parse_unstructured_signal(self,raw_content: str, content_type: str) -> Dict[str,Any]:
        """
        Parse messy unstructured inputs (WhatsApp texts, OCR invoices, voice transcripts)
        into structured JSON using pattern extraction.
        content_type: 'text' | 'ocr_result' | 'stt_transcript'
        """
        return await self.call_tool("parse_unstructured_signal",{
            "raw_content":raw_content,
            "content_type":content_type
        })

    async def query_macro_context(self, indicators: list[str]) -> Dict[str,Any]:
        """
        Fetch macro-economic indicators to adjust risk and logistics weights.
        indicators: list containing any of ['oil_price', 'usd_myr', 'local_inflation']
        """
        return self.call_tool("query_macro_context",{
            "indicators": indicators
        })


    # ─────────────────────────────────────────────
    # PHASE 2 — REASONING & SIMULATION
    # ─────────────────────────────────────────────

    async def simulate_yield_scenario(self,item_id: str, action: str, value: float) -> Dict[str,Any]:
        """
        Simulate the profit impact of a price change or bundle deal.
        action: 'discount' | 'bundle'
        value: discount percentage (0-100) or bundle price
        """
        return await self.call_tool("simulate_yield_scenario",{
            "item_id": item_id,
            "action": action,
            "value": value
        })

    async def evaluate_supply_chain_options(self,item_id: str) -> Dict[str,Any]:
        """
        Compare all suppliers for a given inventory item by total landed cost vs reliability.
        """
        return await self.call_tool("evaluate_supply_chain_options",{
            "item_id": item_id
        })


    async def check_operational_capacity(self, projected_order_surge: int, complexity_factor: int) -> Dict[str,Any]:
        """
        Validate if current staff can handle a projected order surge.
        projected_order_surge: expected additional orders
        complexity_factor: 1 (simple) to 5 (very complex dishes)
        """
        return await self.call_tool("check_operational_capacity",{
            "projected_order_surge": projected_order_surge,
            "complexity_factor": complexity_factor
        })


    # ─────────────────────────────────────────────
    # PHASE 3 — EXECUTION
    # ─────────────────────────────────────────────

    async def execute_operational_action(
        self,
        action_type: str,
        payload: dict,
        p_logic_summary: str,
        r_logic_summary: str,
    ) -> Dict[str,Any]:
        """
        Write tool — executes UPDATE_MENU, CREATE_PO (purchase order), or INVENTORY_ADJUST.
        action_type: 'UPDATE_MENU' | 'CREATE_PO' | 'INVENTORY_ADJUST'
        payload: { target_id, new_value }
        """
        return await self.call_tool("execute_operational_action",{
            "action_type": action_type,
            "payload": payload,
            "p_logic_summary": p_logic_summary,
            "r_logic_summary": r_logic_summary
        })

    async def formulate_marketing_strategy(
        self,
        strategy_type: str,
        config: dict,
        goal: str,
    ) -> Dict[str,Any]:
        """
        Trigger a targeted marketing campaign.
        strategy_type: 'VOUCHER' | 'FLASH_SALE' | 'AD_BOOST'
        goal: 'clear_stock' | 'maximize_margin'
        config: { discount, audience, budget }
        """
        return await self.call_tool("formulate_marketing_strategy",{
            "strategy_type": strategy_type,
            "config": config,
            "goal": goal
        })

    async def send_human_notification(self,priority: str, message: str, proposed_action_json: dict) -> Dict[str,Any]:
        """
        Send an Approve/Reject notification to the human operator for high-stakes decisions.
        priority: 'high' | 'medium'
        Use for: spending > RM500, price changes > 15%, or irreversible actions.
        """
        return self.call_tool("send_human_notification",{
            "priority": priority,
            "message": message,
            "proposed_action_json": proposed_action_json
        })


    # ─────────────────────────────────────────────
    # PHASE 4 — EVOLUTION / MEMORY
    # ─────────────────────────────────────────────

    async def generate_post_mortem_learning(self,event_id: str, actual_outcome: dict) -> Dict[str,Any]:
        """
        Compare expected vs actual outcome, write a lesson into the knowledge base.
        actual_outcome: { revenue, waste_reduced }
        """
        return await self.call_tool("generate_post_mortem_learning",{
            "event_id": event_id,
            "actual_outcome": actual_outcome
        })
