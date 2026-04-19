"""
api/server.py — FastAPI HTTP layer
Exposes the LangGraph agent as REST endpoints for your Flutter/web frontend.

Run: uvicorn api.server:app --reload --port 8080
"""
import uuid
from datetime import datetime
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.graph.graph import get_graph
from langchain_core.messages import HumanMessage
from app.db.client import get_supabase

app = FastAPI(
    title="MEX Agent API",
    description="AI-powered restaurant management agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = get_graph()  # Initialize the agent graph at startup

# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────
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

class NotificationApproval(BaseModel):
    notification_id: str
    approved: bool
    operator_note: Optional[str] = None


# ─────────────────────────────────────────────
# Chat endpoint — main agent entry point
# ─────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    graph = get_graph()

    config = {"configurable": {"thread_id": session_id}}
    
    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "p_agent_position": "",
        "r_agent_position": "",
        "debate_rounds": 0,
        "consensus_reached": False,
        "requires_human_approval": False,
        "decision_type": "direct",
        "final_response": "",
    }

    try:
        input_data = {"messages": [HumanMessage(content=req.message)]}
        result = await graph.ainvoke(input_data, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        session_id=session_id,
        response=result.get("final_response", "No response generated."),
        p_agent_position=result.get("p_agent_position") or None,
        r_agent_position=result.get("r_agent_position") or None,
        debate_rounds=result.get("debate_rounds"),
        timestamp=datetime.utcnow().isoformat(),
    )


# ─────────────────────────────────────────────
# Notifications — human approval queue
# ─────────────────────────────────────────────
@app.get("/notifications")
async def get_notifications(unread_only: bool = True):
    db = get_supabase()
    query = db.table("notifications").select("*").order("created_at", desc=True)
    if unread_only:
        query = query.eq("is_read", False)
    result = query.execute()
    return {"notifications": result.data}


@app.post("/notifications/approve")
async def approve_notification(req: NotificationApproval):
    db = get_supabase()
    db.table("notifications").update({
        "is_read": True,
    }).eq("notification_id", req.notification_id).execute()

    if req.approved:
        # Re-invoke agent with approval context
        graph = get_graph()
        approval_msg = f"Human approved notification {req.notification_id}. Note: {req.operator_note or 'Approved'}. Please execute the proposed action now."
        result = await graph.ainvoke({
            "messages": [HumanMessage(content=approval_msg)],
            "p_agent_position": "", "r_agent_position": "",
            "debate_rounds": 0, "consensus_reached": True,
            "requires_human_approval": False,
            "decision_type": "direct", "final_response": "",
        })
        return {"status": "approved_and_executed", "agent_response": result.get("final_response")}

    return {"status": "rejected"}



@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    try:
        print("🚀 Agent API running at http://127.0.0.1:8080")
        uvicorn.run(app, host="127.0.0.1", port=8080)
    except KeyboardInterrupt:
        print("\n🛑 Mission aborted by user.")
    except Exception as e:
        print(f"\n❌ Critical System Error: {e}")