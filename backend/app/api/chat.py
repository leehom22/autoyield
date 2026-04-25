import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.graph.assistant_graph import get_graph

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    p_agent_position: Optional[str] = None
    r_agent_position: Optional[str] = None
    debate_rounds: Optional[int] = None
    timestamp: str

class RouteInfo(BaseModel):
    decision_type: Optional[str] = None
    decision_domain: Optional[str] = None
    debate_started: bool = False
    consensus_reached: bool = False


class AgentInfo(BaseModel):
    p_agent_position: Optional[str] = None
    r_agent_position: Optional[str] = None
    debate_rounds: int = 0


class ExecutionInfo(BaseModel):
    final_response: Optional[str] = None
    human_approval_sent: bool = False
    decision_saved: bool = False


# class ChatResponse(BaseModel):
#     session_id: str
#     message: str
#     route: RouteInfo
#     agents: AgentInfo
#     execution: ExecutionInfo
#     error: Optional[str] = None
#     timestamp: str

# @router.post("", response_model=ChatResponse)
# async def chat(req: ChatRequest):
#     session_id = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
#     config = {"configurable": {"thread_id": session_id}}
#     graph = get_graph()  
    
#     try:
#         input_data = {"messages": [HumanMessage(content=req.message)]}
#         result = await graph.ainvoke(input_data, config)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

#     return ChatResponse(
#         session_id=session_id,
#         response=result.get("final_response", "No response generated."),
#         p_agent_position=result.get("p_agent_position"),
#         r_agent_position=result.get("r_agent_position"),
#         debate_rounds=result.get("debate_rounds"),
#         timestamp=datetime.now(timezone.utc).isoformat(),
#     )

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    graph = get_graph()

    try:
        input_data = {
            "messages": [HumanMessage(content=req.message)],
            "user_query": req.message,

            "trigger_signal": "CHAT",
            "invoice_data": {},
            "should_persist_decision": False,
            "decision_saved": False,

            "debate_started": False,
            "p_agent_position": "",
            "r_agent_position": "",
            "debate_rounds": 0,
            "consensus_reached": False,

            "decision_type": "unknown",
            "decision_domain": "unknown",
            "pending_handler": "supervisor",
            "supervisor_retries": 0,
            "node_tool_call_count": 0,

            "human_approval_sent": False,
            "supervisor_summary": "",
            "final_response": "",
            "error_state": "",
            "api_response": {},
        }

        result = await graph.ainvoke(input_data, config)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

    api_response = result.get("api_response") or {}
    
    route = api_response.get("route") or {}
    agents = api_response.get("agents") or {}
    execution = api_response.get("execution") or {}

    return ChatResponse(
        session_id=session_id,
        # Note: I changed 'result' to 'api_response' or 'execution' as 'result' was undefined
        response=api_response.get("final_response", "No response generated."),
        p_agent_position=agents.get("p_agent_position"),
        r_agent_position=agents.get("r_agent_position"),
        debate_rounds=route.get("debate_rounds"),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )