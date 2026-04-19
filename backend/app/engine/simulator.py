# app/engine/simulator.py
import asyncio
import json
from datetime import datetime, timedelta
from app.core.state import SYSTEM_STATE
from app.services.order_service import generate_random_order
from app.services.db_service import get_active_menu, insert_mock_order
import random

class WorldSimulationEngine:
    def __init__(self):
        self.is_running = False
        self.is_paused = False       # True when agent is reasoning
        self.simulated_time = datetime.now()   # Start with real current time
        self.tick_real_sec = 1.0     # 1s in real world
        self.tick_sim_min = 30       # Simulate 30 minutes per tick
        self.tick_count = 0
        self.menu_cache = []
        self.active_order_queue = []   # Pending orders in the simulated world
        self.sse_clients = []          # Store in SSE queues

    # Call when agent starts reasoning
    def pause_world(self):
        self.is_paused = True
        print("⏸️ [World] Time stopped. Agent is reasoning...")

    # Call when agent finishes reasoning
    def resume_world(self):
        self.is_paused = False
        print("▶️ [World] Time resumed.")

    async def run_loop(self):
        self.is_running = True
        self.menu_cache = get_active_menu()
        print("🌍 [World Engine] Started. 1 tick = 30 sim minutes.")
        
        while self.is_running:
            if not self.is_paused:
                # 1. Time flow
                self.tick_count += 1
                self.simulated_time += timedelta(minutes=self.tick_sim_min)

                if self.tick_count % 10 == 0:
                    self.menu_cache = get_active_menu()   # Refresh menu to retrieve agent updates in every 10 ticks
                
                # 2. Dynamically generate orders based on Velocity in God Mode
                velocity = SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
                num_to_generate = int(2 * velocity * random.uniform(0.8, 1.2))   # Base 2 orders per tick, scaled by velocity
                
                for _ in range(num_to_generate):
                    order_payload = generate_random_order(self.simulated_time)
                    if order_payload:
                        self.active_order_queue.append(order_payload)
                        # Store into db
                        asyncio.create_task(self._async_db_insert(order_payload))

                # 3. Simulate order processing (Default as 3 orders per tick)
                process_capacity = 3
                self.active_order_queue = self.active_order_queue[process_capacity:]

                # 4. Broadcast current state to SSE clients
                await self.broadcast_state()

            # Sleep for real seconds before next tick
            await asyncio.sleep(self.tick_real_sec)

    async def _async_db_insert(self, data):
        try:
            insert_mock_order(data)
        except Exception as e:
            print(f"[DB Error] Failed to inject order: {e}")

    async def broadcast_state(self):
        # Broadcast Payload Structure for frontend SSE consumption
        payload = {
            "simulated_time": self.simulated_time.strftime("%Y-%m-%d %H:%M"),
            "is_paused": self.is_paused,
            "queue_length": len(self.active_order_queue),
            "velocity": SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
        }
        message = json.dumps(payload)
        
        # Push to SSE clients
        for queue in self.sse_clients:
            await queue.put(message)

# Object instantiation
world_engine = WorldSimulationEngine()