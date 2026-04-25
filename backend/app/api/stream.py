import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.engine.simulator import world_engine

router = APIRouter()

# ========= SSE Endpoint for Real-time World State Streaming =======
# Frontend retrieves simulated time and orders queue

@router.get("/world-state")
async def stream_world_state(request: Request):

    # Generate a unique queue for client connection and register with the world engine
    client_queue = asyncio.Queue()
    async with world_engine._sse_lock:
        world_engine.sse_clients.append(client_queue)
    
    async def event_generator():
        try:
            while True:
                # Stop streaming if client disconnects
                if await request.is_disconnected():
                    break
                
                try:
                    data = await asyncio.wait_for(client_queue.get(), timeout=1.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass
        finally:
            async with world_engine._sse_lock:
                if client_queue in world_engine.sse_clients:
                    # Clean up disconnected client's queue from the world engine
                    world_engine.sse_clients.remove(client_queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")