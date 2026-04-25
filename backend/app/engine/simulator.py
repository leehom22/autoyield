import asyncio
import json
from datetime import datetime, timedelta, timezone
from app.core.state import SYSTEM_STATE
from app.services.order_service import generate_random_order
from app.services.db_service import get_active_menu, insert_mock_order, get_inventory_item, update_inventory_quantity, complete_order_in_db, insert_kds_entry
from app.core.config import settings
import random
import logging
import uuid

logger = logging.getLogger(__name__)

class WorldSimulationEngine:
    def __init__(self):
        self.is_running = False
        self.is_paused = False       # True when agent is reasoning
        self.simulated_time = datetime(2026, 4, 20, 8, 0, tzinfo=timezone.utc)   # Start with 20/4 8a.m. 
        self.tick_real_sec = settings.SIM_TICK_REAL_SEC     # 1s in real world
        self.tick_sim_min = settings.SIM_TICK_SIM_MIN       # Simulate 30 minutes per tick
        self.tick_count = 0
        self.menu_cache = []
        self.active_order_queue = []   # Pending orders in the simulated world
        self.sse_clients = []          # Store in SSE queues
        self._sse_lock = asyncio.Lock()

    # Call when agent starts reasoning
    def pause_world(self):
        self.is_paused = True
        print("⏸️ [World] Time stopped. Agent is reasoning...")

    # Call when agent finishes reasoning
    def resume_world(self):
        self.is_paused = False
        print("▶️ [World] Time resumed.")
    
    # Asynchronously comsume inventory based on order by querying for the recipe of ingredients of the ordered dishes
    async def _consume_inventory_for_order(self, order_data: dict):

        items = order_data.get("items", [])
        if not items:
            return

        # Retrieve menu
        menu_items = await asyncio.to_thread(get_active_menu)
        menu_by_name = {item["name"]: item for item in menu_items}

        for ordered_item in items:
            item_name = ordered_item.get("name")
            if not item_name:
                continue
            menu = menu_by_name.get(item_name)
            if not menu:
                logger.warning(f"Menu item '{item_name}' not found, cannot consume inventory")
                continue

            ingredients = menu.get("ingredients", [])
            if not isinstance(ingredients, list):
                continue

            for ing in ingredients:
                inv_name = ing.get("item_name")
                qty_needed = ing.get("qty", 0.0)
                if not inv_name or qty_needed == 0:
                    continue

                # Check current inventory
                inv_item = await asyncio.to_thread(get_inventory_item, inv_name)
                if not inv_item:
                    logger.warning(f"Inventory item '{inv_name}' not found, skip")
                    continue

                new_qty = inv_item["qty"] - qty_needed
                if new_qty < 0:
                    # Record warning when insufficient stock but persist to sell
                    logger.warning(f"Insufficient stock for {inv_name}: needed {qty_needed}, had {inv_item['qty']}")
                    new_qty = 0

                # Update inventory
                await asyncio.to_thread(
                    update_inventory_quantity,
                    inv_item["id"],
                    new_qty
                )

    async def _async_db_complete(self, order_data: dict):
        try:
            order_id = order_data.get("id")
            kds_id = order_data.get("kds_uuid")
            if order_id and kds_id:
                await asyncio.to_thread(complete_order_in_db, order_id, kds_id)
        except Exception as e:
            logger.error(f"[DB Error] Failed to complete order: {e}")

    async def _async_db_insert(self, order_data: dict):
        try:
            # 1. Copy a clean payload
            db_order_payload = {k: v for k, v in order_data.items() if k != "kds_uuid"}
            await asyncio.to_thread(insert_mock_order, db_order_payload)
            
            # 2. Read KDS ID
            kds_id = order_data.get("kds_uuid")
            if not kds_id:
                return

            # 3. Insert kds_queue table
            prep_minutes = int(10 + (len(self.active_order_queue) / 2))
            eta = (self.simulated_time + timedelta(minutes=prep_minutes)).isoformat()

            kds_payload = {
                "id": str(kds_id),
                "kds_entry_id": f"kds_{order_data['id'][:8]}",
                "order_id": order_data["id"][-6:], 
                "items": order_data["items"],
                "priority": "normal",
                "status": "displayed",
                "estimated_prep_minutes": prep_minutes,
                "position_in_queue": len(self.active_order_queue),
                "eta_timestamp": eta,
                "created_at": order_data["timestamp"]
            }
            await asyncio.to_thread(insert_kds_entry, kds_payload)

            # 4. Consume inventory
            await self._consume_inventory_for_order(order_data)
        except Exception as e:
            logger.error(f"[DB Error] _async_db_insert failed: {e}")


    async def broadcast_state(self):
        # Broadcast Payload Structure for frontend SSE consumption
        print(f"[DEBUG] broadcast_state called, clients: {len(self.sse_clients)}")
        payload = {
            "simulated_time": self.simulated_time.strftime("%Y-%m-%d %H:%M"),
            "is_paused": self.is_paused,
            "queue_length": len(self.active_order_queue),
            "velocity": SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
        }
        message = json.dumps(payload)
        
        # Push to SSE clients
        async with self._sse_lock:
            for queue in self.sse_clients[:]:
                try:
                    await queue.put(message)
                except Exception as e:
                    print(f"SSE broadcast error to queue: {e}")
                    if queue in self.sse_clients:
                        self.sse_clients.remove(queue)

    
    async def run_loop(self):
        self.is_running = True
        self.is_paused = False
        self.menu_cache = await asyncio.to_thread(get_active_menu)
        print("🌍 [World Engine] Started. 1 tick = 30 sim minutes.")
        
        while self.is_running:
            print(f"[DEBUG] loop iteration, is_paused={self.is_paused}") 
            if not self.is_paused:
                # 1. Time flow
                self.tick_count += 1
                self.simulated_time += timedelta(minutes=self.tick_sim_min)

                if self.tick_count % 10 == 0:
                    self.menu_cache = await asyncio.to_thread(get_active_menu)   # Refresh menu to retrieve agent updates in every 10 ticks

                process_capacity = settings.SIM_ORDER_PROCESS_CAPACITY
                orders_to_complete = self.active_order_queue[:process_capacity]
                for po in orders_to_complete:
                    asyncio.create_task(self._async_db_complete(po))
                self.active_order_queue = self.active_order_queue[process_capacity:]
                
                # 2. Dynamically generate orders based on Velocity in God Mode
                velocity = SYSTEM_STATE.get("order_velocity_multiplier", 1.0)
                # num_to_generate = int(settings.SIM_BASE_ORDERS_PER_TICK * velocity * random.uniform(0.8, 1.2))   # Base 2 orders per tick, scaled by velocity
                # 60% prob to have an order per tick
                prob = 0.6 * velocity
                num_to_generate = 0
                
                # Prob > 1, generate whole number part
                num_to_generate += int(prob)
                if random.random() < (prob - int(prob)):
                    num_to_generate += 1

                for _ in range(num_to_generate):
                    order_payload = generate_random_order(self.simulated_time)
                    if order_payload:
                        order_payload["kds_uuid"] = str(uuid.uuid4())
                        self.active_order_queue.append(order_payload)
                        # Store into db
                        asyncio.create_task(self._async_db_insert(order_payload))

                # 3. Simulate order processing (Default as 3 orders per tick)
                # process_capacity = settings.SIM_ORDER_PROCESS_CAPACITY
                # orders_to_complete = self.active_order_queue[:process_capacity]
                # for po in orders_to_complete:
                #     asyncio.create_task(self._async_db_complete(po))
                # self.active_order_queue = self.active_order_queue[process_capacity:]

                # 4. Broadcast current state to SSE clients
                await self.broadcast_state()

            # Sleep for real seconds before next tick
            await asyncio.sleep(self.tick_real_sec)

# Object instantiation
world_engine = WorldSimulationEngine()

# For synchronize the global datetime
def get_current_simulated_time() -> datetime:
    return world_engine.simulated_time
