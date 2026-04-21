import asyncio
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core.supabase import supabase
from app.core.crisis_monitor import crisis_monitor_loop
from app.graph.graph import get_graph
from langchain_core.messages import HumanMessage
from IPython.display import Image, display
# Imports from your second file
from app.engine.simulator import world_engine
from app.api import stream, sandbox, agent, webhook
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.api import chat
from app.api import permission

from app.core.supabase import supabase
from app.graph.forecast_graph import build_forecast_graph
from app.graph.proactive_graph import build_proactive_graph

forecast_graph = build_forecast_graph()
proactive_graph = build_proactive_graph()
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
# Lifespan Management (Startup/Shutdown)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the World Simulation Engine
    engine_task = asyncio.create_task(world_engine.run_loop())
    print("✅ AutoYield Kernel started. World simulation engine is running.")
    
    # Initialize the Agent Graph, Scheduler and Proactive Monitoring globally once
    app.state.graph = get_graph()
    start_scheduler(app.state.graph)
    monitor_task = asyncio.create_task(crisis_monitor_loop(app))
    
    yield
    
    # Shutdown: Stop all the engine and tasks
    shutdown_scheduler()
    world_engine.is_running = False
    monitor_task.cancel()
    try:
        await asyncio.wait_for(engine_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        print("🛑 World simulation engine shut down.")

# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────
app = FastAPI(
    title="AutoYield Dual-Agent Kernel",
    description="Autonomous F&B Profit & Operations Kernel + AI Agent API",
    version="2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Human-in-the-Loop (Notifications)
# ─────────────────────────────────────────────
@app.get("/api/notifications", tags=["Operator"])
async def get_notifications(unread_only: bool = True):
    db = supabase()
    query = db.table("notifications").select("*").order("created_at", desc=True)
    query = supabase.table("notifications").select("*").order("created_at", desc=True)
    if unread_only:
        query = query.eq("is_read", False)
    result = query.execute()
    return {"notifications": result.data}

@app.post("/api/notifications/approve", tags=["Operator"])
async def approve_notification(req: NotificationApproval):
    db = supabase()
    db.table("notifications").update({"is_read": True}).eq("notification_id", req.notification_id).execute()
    supabase.table("notifications").update({"is_read": True}).eq("notification_id", req.notification_id).execute()

    if req.approved:
        approval_msg = f"Human approved notification {req.notification_id}. Note: {req.operator_note or 'Approved'}. Execute action."
        result = await app.state.graph.ainvoke(
            {"messages": [HumanMessage(content=approval_msg)]},
            {"configurable": {"thread_id": "system_approval"}}
        )
        return {"status": "approved_and_executed", "agent_response": result.get("final_response")}
    return {"status": "rejected"}

# ─────────────────────────────────────────────
# Include Routers from existing modules
# ─────────────────────────────────────────────
app.include_router(chat.router, prefix="/api", tags=["Chatbot"])
app.include_router(sandbox.router, prefix="/api/sandbox", tags=["God Mode"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent Interact"])
# app.include_router(webhook.router, prefix="/api/webhooks", tags=["Internal Triggers"])   Currently replaced by crisis_monitor
app.include_router(stream.router, prefix="/api/stream", tags=["SSE Streaming"])
app.include_router(permission.router, prefix="/api/permissions", tags=["Authorization Panel"])

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    import uvicorn
    import os

    # Create a folder for diagrams if it doesn't exist
    os.makedirs("diagrams", exist_ok=True)

    try:
        # Save Forecast Graph
        with open("diagrams/forecast_graph.png", "wb") as f:
            f.write(forecast_graph.get_graph().draw_mermaid_png())
        
        # Save Proactive Graph
        with open("diagrams/proactive_graph.png", "wb") as f:
            f.write(proactive_graph.get_graph().draw_mermaid_png())
            
        print("✅ Graph visualizations saved to /diagrams folder.")
    except Exception as e:
        print(f"⚠️ Visualization skipped: {e}")

    # Start the FastAPI server
    uvicorn.run(app, host="127.0.0.1", port=8080)