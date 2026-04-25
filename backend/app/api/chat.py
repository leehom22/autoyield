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

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    graph = get_graph()  
    
    try:
        input_data = {"messages": [HumanMessage(content=req.message)]}
        result = await graph.ainvoke(input_data, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

    return ChatResponse(
        session_id=session_id,
        response=result.get("final_response", "No response generated."),
        p_agent_position=result.get("p_agent_position"),
        r_agent_position=result.get("r_agent_position"),
        debate_rounds=result.get("debate_rounds"),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )