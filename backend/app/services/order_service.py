import random
from datetime import datetime
from app.services.db_service import get_active_menu, insert_mock_order
import uuid

# Generate a random order based on the active menu with 1-3 items, revenue, margin and customer segment

def generate_random_order(simulated_time: datetime):
    
    menu_items = get_active_menu()
    if not menu_items:
        return None

    # Random 1-3 items
    num_items = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
    selected_items = random.sample(menu_items, min(num_items, len(menu_items)))

    order_items = []
    total_revenue = 0.0
    total_margin = 0.0

    for item in selected_items:
        price = float(item['current_price'])
        margin_p = float(item['margin_percent']) / 100.0
        
        order_items.append({
            "id": item['id'],
            "name": item['name'],
            "price": price
        })
        total_revenue += price
        total_margin += (price * margin_p)

    # Categoize customer into segments with weighted probabilities distribution
    segments = ['Regular', 'VIP', 'New', 'ChurnRisk']
    segment_weights = [0.6, 0.1, 0.2, 0.1]
    
    order_id = str(uuid.uuid4())
    
    order_data = {
        "id": order_id,
        "items": order_items,
        "total_revenue": round(total_revenue, 2),
        "total_margin": round(total_margin, 2),
        "timestamp": simulated_time.isoformat(),
        "customer_segment": random.choices(segments, weights=segment_weights)[0],
        "order_status": "pending"
    }

    return order_data