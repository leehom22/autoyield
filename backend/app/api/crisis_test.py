from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.graph.proactive_graph import get_proactive_graph
from app.graph.forecast_graph import get_forecast_graph

router = APIRouter(
    prefix="/crisis-test",
    tags=["Crisis Test"]
)


class CrisisTestRequest(BaseModel):
    crisis_type: str
    message: str


@router.post("")
async def trigger_crisis_test(req: CrisisTestRequest):

    try:
        # -------------------------
        # Inventory / Order Crisis
        # -------------------------
        if req.crisis_type in [
            "inventory",
            "order_surge"
        ]:

            graph = get_proactive_graph()

            result = await graph.ainvoke({
                "messages": [
                    HumanMessage(
                        content=f"TEST CRISIS: {req.message}"
                    )
                ],

                "direct_route": "crisis_optimizer",
                "crisis_message": req.message,

                "anomaly_type": "unknown",
                "pending_handler": "crisis_optimizer",

                "margin_summary": "",
                "capacity_summary": "",
                "menu_rewrite_summary": "",
                "kds_summary": "",
                "final_response": "",

                "action_taken": False,
                "node_tool_call_count": 0,
            })

            return {
                "graph_used": "proactive_graph",
                "crisis_type": req.crisis_type,
                "final_response": result.get("final_response"),
                "state": result
            }

        # -------------------------
        # Macro Crisis
        # -------------------------
        elif req.crisis_type in [
            "oil_spike",
            "inflation",
            "macro"
        ]:

            graph = get_forecast_graph()

            result = await graph.ainvoke({
                "messages": [
                    HumanMessage(
                        content=f"TEST MACRO CRISIS: {req.message}"
                    )
                ],

                "forecast_path": "crisis",
                "user_query": req.message,
                "signal_summary": req.message,

                "reorder_plan": "",
                "kitchen_warning": "",
                "constraint_summary": "",
                "revised_plan": "",
                "forecast_result": "",

                "macro_risk_level": "high",
                "plan_generated": False,

                "debate_started": False,
                "p_agent_position": "",
                "r_agent_position": "",
                "debate_rounds": 0,
                "consensus_reached": False,

                "pending_handler": "crisis_optimizer",
                "notification_sent": False,
                "notification_id": "",
                "node_tool_call_count": 0,
            })

            return {
                "graph_used": "forecast_graph",
                "crisis_type": req.crisis_type,
                "forecast_result": result.get("forecast_result"),
                "p_agent_position": result.get("p_agent_position"),
                "r_agent_position": result.get("r_agent_position"),
                "debate_rounds": result.get("debate_rounds"),
                "consensus_reached": result.get("consensus_reached"),
                "state": result
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Use inventory | order_surge | oil_spike | inflation"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )