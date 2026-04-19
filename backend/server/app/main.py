import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.engine.simulator import world_engine
from app.api import stream
from app.core.state import SYSTEM_STATE

# API Routers Register
from app.api import sandbox, agent, webhook

# Global System State for Gode Mode
# SYSTEM_STATE = {
#     "order_velocity_multiplier": 1.0
# }

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    engine_task = asyncio.create_task(world_engine.run_loop())
    print("✅ AutoYield Kernel started. World simulation engine is running.")
    yield
    # Shutdown
    world_engine.is_running = False
    try:
        await engine_task
    except asyncio.CancelledError:
        print("🛑 World simulation engine shut down.")

app = FastAPI(
    title="AutoYield Dual-Agent Kernel",
    description="Autonomous F&B Profit & Operations Kernel",
    version="2.0",
    lifespan=lifespan
)

# Global CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(sandbox.router, prefix="/api/sandbox", tags=["God Mode"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent Interact"])
app.include_router(webhook.router, prefix="/api/webhooks", tags=["Internal Triggers"])
app.include_router(stream.router, prefix="/api/stream", tags=["SSE Streaming"])