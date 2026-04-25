from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.graph.forecast_graph import get_forecast_graph

router = APIRouter(prefix="", tags=["Forecast Test"])


class ForecastTestRequest(BaseModel):
    message: str = "Weekly procurement report analysis required. Review last 7 days of purchases. Provide summary and recommendations."
    forecast_path: str = "standard"  # standard | crisis


@router.post("/weekly-forecast")
async def test_weekly_forecast(req: ForecastTestRequest):
    graph = get_forecast_graph()

    try:
        result = await graph.ainvoke({
            "messages": [HumanMessage(content=req.message)],

            "forecast_path": req.forecast_path,
            "reorder_plan": "",
            "kitchen_warning": "",
            "constraint_summary": "",
            "revised_plan": "",

            "user_query": req.message,
            "signal_summary": "",
            "forecast_result": "",

            "macro_risk_level": "unknown",
            "plan_generated": False,

            "pending_handler": "supervisor",
            "notification_sent": False,
            "notification_id": "",
            "node_tool_call_count": 0,

            "p_agent_position": "",
            "r_agent_position": "",
            "debate_rounds": 0,
            "consensus_reached": False,
            "debate_started": False,

            "decision_saved": False,
        })

        return {
            "status": "success",
            "forecast_path": result.get("forecast_path"),
            "forecast_result": result.get("forecast_result"),
            "p_agent_position": result.get("p_agent_position"),
            "r_agent_position": result.get("r_agent_position"),
            "debate_rounds": result.get("debate_rounds"),
            "consensus_reached": result.get("consensus_reached"),
            "decision_saved": result.get("decision_saved"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))