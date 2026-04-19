-- ======================================================
-- AUTO-YIELD: MOCK DATA (ENGLISH, REALISTIC SNAPSHOT)
-- ======================================================
-- Run this AFTER the final schema is created.
-- All UUIDs are generated dynamically; no manual IDs needed.

-- ======================================================
-- 1. INVENTORY (20 items, various expiry & stock levels)
-- ======================================================
WITH inventory_insert AS (
  INSERT INTO inventory (name, qty, unit, unit_cost, base_price, current_price, expiry_timestamp, min_stock_level, category, version) VALUES
    ('Atlantic Salmon Fillet', 28.5, 'kg', 28.50, 45.00, 42.00, NOW() + INTERVAL '2 days', 10.0, 'Seafood', 0),
    ('Sea Bass Whole', 9.2, 'kg', 22.00, 38.00, 38.00, NOW() + INTERVAL '5 days', 5.0, 'Seafood', 0),
    ('Black Tiger Prawns', 42.0, 'kg', 35.00, 55.00, 52.00, NOW() + INTERVAL '4 days', 8.0, 'Seafood', 0),
    ('Chicken Breast', 65.0, 'kg', 8.50, 15.00, 14.50, NOW() + INTERVAL '8 days', 15.0, 'Meat', 0),
    ('Beef Ribeye', 12.3, 'kg', 42.00, 68.00, 65.00, NOW() + INTERVAL '3 days', 6.0, 'Meat', 0),
    ('Lamb Chop', 7.5, 'kg', 38.00, 60.00, 58.00, NOW() + INTERVAL '2 days', 4.0, 'Meat', 0),
    ('Organic Mixed Vegetables', 95.0, 'kg', 4.20, 7.50, 7.20, NOW() + INTERVAL '1 day', 20.0, 'Vegetables', 0),
    ('Heirloom Tomatoes', 38.0, 'kg', 5.80, 9.90, 9.50, NOW() + INTERVAL '2 days', 10.0, 'Vegetables', 0),
    ('Basmati Rice', 180.0, 'kg', 2.50, 4.50, 4.20, NOW() + INTERVAL '45 days', 30.0, 'Dry Goods', 0),
    ('Spaghetti Pasta', 70.0, 'kg', 1.80, 3.20, 3.00, NOW() + INTERVAL '30 days', 20.0, 'Dry Goods', 0),
    ('Parmesan Cheese', 8.2, 'kg', 15.00, 28.00, 26.00, NOW() + INTERVAL '6 days', 3.0, 'Dairy', 0),
    ('Unsalted Butter', 25.0, 'kg', 6.50, 12.00, 11.50, NOW() + INTERVAL '10 days', 8.0, 'Dairy', 0),
    ('Fresh Milk', 32.0, 'L', 1.20, 2.50, 2.30, NOW() + INTERVAL '3 days', 15.0, 'Dairy', 0),
    ('Coca-Cola (Can)', 320.0, 'pcs', 0.60, 1.50, 1.50, NOW() + INTERVAL '60 days', 100.0, 'Beverages', 0),
    ('Craft Beer (IPA)', 110.0, 'pcs', 2.20, 5.00, 4.80, NOW() + INTERVAL '25 days', 40.0, 'Beverages', 0),
    ('Lemon Juice', 15.0, 'L', 3.00, 5.50, 5.00, NOW() + INTERVAL '5 days', 5.0, 'Beverages', 0),
    ('Garlic', 22.0, 'kg', 4.00, 7.00, 6.50, NOW() + INTERVAL '12 days', 5.0, 'Vegetables', 0),
    ('Olive Oil (Extra Virgin)', 28.0, 'L', 9.50, 18.00, 17.00, NOW() + INTERVAL '80 days', 8.0, 'Dry Goods', 0),
    ('Flour (All Purpose)', 85.0, 'kg', 0.90, 1.80, 1.70, NOW() + INTERVAL '100 days', 20.0, 'Dry Goods', 0),
    ('Vanilla Ice Cream', 18.0, 'L', 4.00, 7.50, 7.00, NOW() + INTERVAL '14 days', 5.0, 'Dessert', 0)
  RETURNING id, name
),
-- ======================================================
-- 2. MENU ITEMS (with ingredients JSONB referencing inventory names)
-- ======================================================
menu_insert AS (
  INSERT INTO menu_items (name, ingredients, base_price, current_price, margin_percent, status, category)
  SELECT
    m.name,
    m.ingredients_json,
    m.base_price,
    m.current_price,
    ROUND(((m.current_price - m.cost_per_unit) / m.current_price) * 100, 2),
    'active',
    m.category
  FROM (
    VALUES
      ('Grilled Salmon',
       jsonb_build_array(jsonb_build_object('item_name', 'Atlantic Salmon Fillet', 'qty', 0.2)),
       45.00, 42.00, 5.70, 'Main'),
      ('Seabass Aglio Olio',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Sea Bass Whole', 'qty', 0.25),
         jsonb_build_object('item_name', 'Spaghetti Pasta', 'qty', 0.15),
         jsonb_build_object('item_name', 'Olive Oil', 'qty', 0.02),
         jsonb_build_object('item_name', 'Garlic', 'qty', 0.01)
       ),
       38.00, 36.00, 7.20, 'Main'),
      ('Garlic Butter Prawns',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Black Tiger Prawns', 'qty', 0.15),
         jsonb_build_object('item_name', 'Unsalted Butter', 'qty', 0.03),
         jsonb_build_object('item_name', 'Garlic', 'qty', 0.01)
       ),
       55.00, 52.00, 8.50, 'Main'),
      ('Chicken Parmigiana',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Chicken Breast', 'qty', 0.2),
         jsonb_build_object('item_name', 'Parmesan Cheese', 'qty', 0.05),
         jsonb_build_object('item_name', 'Flour', 'qty', 0.02)
       ),
       18.50, 17.90, 3.20, 'Main'),
      ('Ribeye Steak',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Beef Ribeye', 'qty', 0.3),
         jsonb_build_object('item_name', 'Unsalted Butter', 'qty', 0.02),
         jsonb_build_object('item_name', 'Garlic', 'qty', 0.01)
       ),
       68.00, 65.00, 12.60, 'Main'),
      ('Lamb Chop with Veg',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Lamb Chop', 'qty', 0.25),
         jsonb_build_object('item_name', 'Organic Mixed Vegetables', 'qty', 0.15)
       ),
       60.00, 58.00, 9.50, 'Main'),
      ('Garden Fresh Salad',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Organic Mixed Vegetables', 'qty', 0.1),
         jsonb_build_object('item_name', 'Heirloom Tomatoes', 'qty', 0.05)
       ),
       9.90, 9.50, 1.20, 'Appetizer'),
      ('Tomato Bruschetta',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Heirloom Tomatoes', 'qty', 0.08),
         jsonb_build_object('item_name', 'Olive Oil', 'qty', 0.01),
         jsonb_build_object('item_name', 'Garlic', 'qty', 0.005)
       ),
       8.50, 8.00, 1.40, 'Appetizer'),
      ('Cheese Platter',
       jsonb_build_array(jsonb_build_object('item_name', 'Parmesan Cheese', 'qty', 0.1)),
       14.00, 13.50, 2.10, 'Appetizer'),
      ('Butter Garlic Rice',
       jsonb_build_array(
         jsonb_build_object('item_name', 'Basmati Rice', 'qty', 0.2),
         jsonb_build_object('item_name', 'Unsalted Butter', 'qty', 0.02)
       ),
       5.00, 4.80, 0.90, 'Side'),
      ('French Fries',
       jsonb_build_array(jsonb_build_object('item_name', 'Organic Mixed Vegetables', 'qty', 0.15)),
       6.50, 6.20, 1.30, 'Side'),
      ('Coke (Can)',
       jsonb_build_array(jsonb_build_object('item_name', 'Coca-Cola (Can)', 'qty', 1)),
       1.50, 1.50, 0.90, 'Beverage'),
      ('Craft Beer',
       jsonb_build_array(jsonb_build_object('item_name', 'Craft Beer (IPA)', 'qty', 1)),
       5.00, 4.80, 1.30, 'Beverage'),
      ('Lemonade',
       jsonb_build_array(jsonb_build_object('item_name', 'Lemon Juice', 'qty', 0.05)),
       4.50, 4.20, 1.50, 'Beverage'),
      ('Vanilla Ice Cream Cup',
       jsonb_build_array(jsonb_build_object('item_name', 'Vanilla Ice Cream', 'qty', 0.15)),
       7.50, 7.00, 1.40, 'Dessert')
  ) AS m(name, ingredients_json, base_price, current_price, cost_per_unit, category)
  RETURNING id, name, ingredients
),
-- ======================================================
-- 3. SUPPLIERS
-- ======================================================
supplier_insert AS (
  INSERT INTO suppliers (name, categories, reliability_score, avg_lead_time, min_order_qty, pricing_tiers) VALUES
    ('Oceanic Seafood Supply', ARRAY['Seafood'], 0.95, 12.0, 20.0, '{"1-50": 28.50, "51-200": 26.00, "201+": 24.00}'::JSONB),
    ('Prime Meat Co.', ARRAY['Meat'], 0.92, 18.0, 15.0, '{"1-30": 42.00, "31-100": 39.00, "101+": 36.50}'::JSONB),
    ('Green Valley Produce', ARRAY['Vegetables'], 0.88, 10.0, 10.0, '{"1-50": 4.20, "51-200": 3.90, "201+": 3.60}'::JSONB),
    ('Global Grains & Dry', ARRAY['Dry Goods'], 0.97, 24.0, 50.0, '{"1-100": 2.50, "101-500": 2.20, "501+": 2.00}'::JSONB),
    ('DairyPure Malaysia', ARRAY['Dairy'], 0.90, 8.0, 20.0, '{"1-40": 6.50, "41-150": 5.90, "151+": 5.40}'::JSONB),
    ('BevX Beverages', ARRAY['Beverages'], 0.99, 6.0, 100.0, '{"1-200": 0.60, "201-1000": 0.55, "1001+": 0.50}'::JSONB),
    ('Local Artisan Dairy', ARRAY['Dairy','Dessert'], 0.85, 5.0, 5.0, '{"1-20": 15.00, "21-50": 14.00}'::JSONB),
    ('Premium Oil & Spice', ARRAY['Dry Goods'], 0.94, 14.0, 12.0, '{"1-30": 9.50, "31-80": 8.80, "81+": 8.20}'::JSONB)
  RETURNING id, name
),
-- ======================================================
-- 4. PROCUREMENT LOGS (recent orders from suppliers)
-- ======================================================
procurement_insert AS (
  INSERT INTO procurement_logs (item_id, supplier_id, qty, unit_cost, delivery_status, arrival_estimate)
  SELECT
    i.id,
    s.id,
    ROUND((random() * 50 + 10)::numeric, 1),
    i.unit_cost * (0.9 + random() * 0.2),
    (ARRAY['delivered', 'in_transit', 'ordered'])[floor(random() * 3) + 1],
    NOW() + (random() * INTERVAL '10 days')
  FROM inventory i
  CROSS JOIN LATERAL (SELECT id FROM suppliers ORDER BY random() LIMIT 1) s
  WHERE random() < 0.4   -- about 8 logs
  LIMIT 25
),
-- ======================================================
-- 5. STAFF ROSTER (with precise timestamps for Friday)
-- ======================================================
staff_insert AS (
  INSERT INTO staff_roster (name, role, hourly_rate, shift_start, shift_end, max_capacity_score, current_load) VALUES
    ('James Wong', 'Head Chef', 35.00, '2026-04-18 08:00:00+08', '2026-04-18 20:00:00+08', 0.95, 0.70),
    ('Sarah Lim', 'Sous Chef', 28.00, '2026-04-18 12:00:00+08', '2026-04-18 22:00:00+08', 0.90, 0.60),
    ('Ahmad Faiz', 'Line Cook', 18.00, '2026-04-18 09:00:00+08', '2026-04-18 17:00:00+08', 0.80, 0.85),
    ('Mei Ling', 'Pastry Chef', 22.00, '2026-04-18 07:00:00+08', '2026-04-18 15:00:00+08', 0.85, 0.50),
    ('Raj Kumar', 'Kitchen Helper', 12.00, '2026-04-18 10:00:00+08', '2026-04-18 19:00:00+08', 0.75, 0.90),
    ('Tan Wei', 'Service Manager', 30.00, '2026-04-18 11:00:00+08', '2026-04-18 23:00:00+08', 0.92, 0.40),
    ('Lisa Ng', 'Bartender', 16.00, '2026-04-18 17:00:00+08', '2026-04-19 02:00:00+08', 0.88, 0.65),  -- crosses midnight
    ('Kumar S', 'Dishwasher', 10.00, '2026-04-18 14:00:00+08', '2026-04-18 22:00:00+08', 0.70, 0.80),
    ('Priya K', 'Server', 8.50, '2026-04-18 11:00:00+08', '2026-04-18 20:00:00+08', 0.82, 0.75),
    ('Chen Hao', 'Server', 8.50, '2026-04-18 17:00:00+08', '2026-04-19 01:00:00+08', 0.82, 0.60)
),
-- ======================================================
-- 6. MARKET TRENDS HISTORY (last 7 days for oil, USD/MYR, inflation)
-- ======================================================
market_insert AS (
  INSERT INTO market_trends_history (indicator, value, recorded_at) VALUES
    ('oil_price', 82.5, NOW() - INTERVAL '7 days'),
    ('oil_price', 83.1, NOW() - INTERVAL '6 days'),
    ('oil_price', 83.8, NOW() - INTERVAL '5 days'),
    ('oil_price', 84.2, NOW() - INTERVAL '4 days'),
    ('oil_price', 84.9, NOW() - INTERVAL '3 days'),
    ('oil_price', 85.1, NOW() - INTERVAL '2 days'),
    ('oil_price', 85.4, NOW() - INTERVAL '1 day'),
    ('oil_price', 85.4, NOW()),
    ('usd_myr', 4.68, NOW() - INTERVAL '7 days'),
    ('usd_myr', 4.69, NOW() - INTERVAL '6 days'),
    ('usd_myr', 4.70, NOW() - INTERVAL '5 days'),
    ('usd_myr', 4.70, NOW() - INTERVAL '4 days'),
    ('usd_myr', 4.71, NOW() - INTERVAL '3 days'),
    ('usd_myr', 4.72, NOW() - INTERVAL '2 days'),
    ('usd_myr', 4.72, NOW() - INTERVAL '1 day'),
    ('usd_myr', 4.72, NOW()),
    ('local_inflation', 2.6, NOW() - INTERVAL '30 days'),
    ('local_inflation', 2.7, NOW() - INTERVAL '20 days'),
    ('local_inflation', 2.8, NOW() - INTERVAL '10 days'),
    ('local_inflation', 2.8, NOW())
),
-- ======================================================
-- 7. MARKETING CAMPAIGNS (active & past)
-- ======================================================
campaign_insert AS (
  INSERT INTO marketing_campaigns (type, trigger_event, spend, revenue_uplift, active_status, roi_actual) VALUES
    ('VOUCHER', 'inventory_low_salmon', 120.00, 450.00, true, 2.75),
    ('FLASH_SALE', 'expiry_risk_cheese', 80.00, 320.00, true, 3.00),
    ('AD_BOOST', 'weekend_surge', 200.00, 890.00, true, 3.45),
    ('BUNDLE', 'new_menu_launch', 150.00, 610.00, false, NULL),
    ('VOUCHER', 'churn_risk_segment', 90.00, 280.00, true, 2.11)
),
-- ======================================================
-- 8. ORDERS (150 realistic orders from last 2 days, including today)
-- ======================================================
order_insert AS (
  INSERT INTO orders (items, total_revenue, total_margin, timestamp, customer_segment)
  SELECT
    jsonb_build_array(
      jsonb_build_object('name', menu_name, 'price', menu_price)
    ) AS items,
    menu_price AS total_revenue,
    menu_price * 0.45 AS total_margin,
    ts,
    seg
  FROM (
    SELECT 
      unnest(ARRAY['Grilled Salmon', 'Ribeye Steak', 'Chicken Parmigiana', 'Lemonade', 'Craft Beer', 'Garden Fresh Salad', 'Vanilla Ice Cream Cup']) AS menu_name,
      unnest(ARRAY[42.00, 65.00, 17.90, 4.20, 4.80, 9.50, 7.00]) AS menu_price,
      generate_series(1, 150) AS idx,
      NOW() - (random() * INTERVAL '2 days') AS ts,
      (ARRAY['VIP', 'New', 'ChurnRisk', 'Regular'])[floor(random() * 4) + 1] AS seg
  ) t
  WHERE random() < 0.9   -- some rows may be omitted to keep realistic
  LIMIT 150
),





-- Assume that no decision logs and knowledge base entries exist before agent starts running, just save for backup here

-- ======================================================
-- 9. DECISION LOGS (P-Agent vs R-Agent debates)
-- ======================================================
decision_insert AS (
  INSERT INTO decision_logs (timestamp, trigger_signal, p_agent_argument, r_agent_argument, resolution, action_taken) VALUES
    (NOW() - INTERVAL '5 days', 'salmon_stock_days < 1.5', 
     'P-Agent: Raise price by 15% to protect margin. Current margin 42%, new margin 48%. Demand elasticity low on weekends.', 
     'R-Agent: Switch to sea bass special + 10% flash sale. Customer loyalty risk high. Use voucher for regulars.', 
     'Hybrid: Sea bass flash sale 15%, keep salmon for VIP only.', 
     'UPDATE_MENU: added sea bass promo, hidden salmon from regular menu'),
    (NOW() - INTERVAL '4 days', 'oil_price_surge +5%', 
     'P-Agent: Increase delivery fee and raise all meat dishes by RM2. Protect net profit.', 
     'R-Agent: Renegotiate with local supplier (Green Valley). Bundle veg+meat to absorb cost.', 
     'Adopt R-Agent: local supplier switch + bundle.', 
     'CREATE_PO: local supplier, new bundle "Steak & Veg Set"'),
    (NOW() - INTERVAL '3 days', 'staff_overtime > 30%', 
     'P-Agent: Reduce menu complexity, remove 3 low-margin items.', 
     'R-Agent: Hire part-time helper for RM15/hr, keep full menu.', 
     'P-Agent wins – menu simplified.', 
     'UPDATE_MENU: deactivated 3 items'),
    (NOW() - INTERVAL '2 days', 'beef_ribeye_expiry_48h', 
     'P-Agent: 20% flash sale + social media ad (budget RM80).', 
     'R-Agent: Transform into "Beef Bowl" lunch special, RM25 flat.', 
     'Flash sale approved.', 
     'MARKETING: flash sale campaign created'),
    (NOW() - INTERVAL '1 day', 'customer_churn_rate_up', 
     'P-Agent: Increase loyalty points, but reduce voucher discount.', 
     'R-Agent: Personalized WhatsApp offer for at-risk segment.', 
     'R-Agent: WhatsApp campaign launched.', 
     'send_human_notification: manager approved'),
    (NOW() - INTERVAL '12 days', 'inflation_news', 
     'P-Agent: blanket +5% price increase.', 
     'R-Agent: shrink portion sizes by 8%, keep prices.', 
     'R-Agent wins (less visible to customer).', 
     'INVENTORY_ADJUST: recipe scaling changed'),
    (NOW() - INTERVAL '9 days', 'supplier_delay_chicken', 
     'P-Agent: source from backup supplier (cost +12%).', 
     'R-Agent: swap chicken with tofu special for 3 days.', 
     'Hybrid: tofu special + small backup order.', 
     'CREATE_PO: tofu from local market'),
    (NOW() - INTERVAL '7 days', 'flash_sale_success', 
     'P-Agent: repeat same tactic weekly.', 
     'R-Agent: analyse elasticity first; might fatigue customers.', 
     'R-Agent: pause, analyse data.', 
     'DECISION_LOG: analysis queued'),
    (NOW() - INTERVAL '6 days', 'cheese_overstock', 
     'P-Agent: bundle cheese with wine at 30% off.', 
     'R-Agent: donate to food bank for tax write-off + PR.', 
     'P-Agent bundle executed.', 
     'MARKETING: bundle campaign'),
    (NOW() - INTERVAL '1 hours', 'staff_sick_leave', 
     'P-Agent: close one section of restaurant.', 
     'R-Agent: cross-train servers to help kitchen.', 
     'Cross-training implemented.', 
     'send_human_notification: schedule change')
),
-- ======================================================
-- 10. KNOWLEDGE BASE (RAG lessons with zero vectors initially)
-- ======================================================
knowledge_insert AS (
  INSERT INTO knowledge_base (embedding_vector, scenario_description, lesson_learned, performance_score) VALUES
    ('[0]'::vector, 'Salmon stock critically low before weekend', 'High discount on salmon failed due to rainy weather; instead, cross-sell seabass worked better.', 0.78),
    ('[0]'::vector, 'Oil price spike +5% in one week', 'Switching to local supplier saved 8% logistics cost, but bundle offer was more effective than price hike.', 0.92),
    ('[0]'::vector, 'Staff overtime crisis', 'Simplifying menu by removing 3 low-margin items reduced kitchen load by 22% without losing revenue.', 0.85),
    ('[0]'::vector, 'Flash sale on beef ribeye', '20% discount moved 90% of expiring stock, but margin dropped 6%. Better to transform into lunch special next time.', 0.65),
    ('[0]'::vector, 'Churn risk segment triggered', 'Personalized WhatsApp voucher had 32% redemption vs 12% for generic email. Invest in segmentation.', 0.88),
    ('[0]'::vector, 'Inflation pressure on dairy', 'Shrinking portion size by 8% went unnoticed and preserved margin. Better than price increase.', 0.91),
    ('[0]'::vector, 'Supplier delay for chicken', 'Tofu special was a hit – vegetarian sales up 40% during those 3 days.', 0.83),
    ('[0]'::vector, 'Cheese overstock', 'Bundling with wine gave 2.1x ROI vs donation. But donation improved brand sentiment.', 0.77),
    ('[0]'::vector, 'Labour shortage due to holiday', 'Cross-training servers as runners increased table turnover by 15% without extra hire.', 0.89),
    ('[0]'::vector, 'New menu launch', 'Soft launch with limited items and staff sampling reduced waste by 60% compared to full launch.', 0.94)
),




-- ======================================================
-- 11. INVENTORY PRICING HISTORY (for 5 items, last 3 price changes)
-- ======================================================
pricing_history_insert AS (
  INSERT INTO inventory_pricing_history (inventory_id, unit_cost, current_price, effective_from)
  SELECT 
    id,
    unit_cost,
    current_price,
    NOW() - (random() * INTERVAL '30 days')
  FROM inventory
  WHERE name IN ('Atlantic Salmon Fillet', 'Beef Ribeye', 'Basmati Rice', 'Parmesan Cheese', 'Olive Oil')
  UNION ALL
  SELECT 
    id,
    unit_cost * 0.95,
    current_price * 0.95,
    NOW() - (random() * INTERVAL '60 days')
  FROM inventory
  WHERE name IN ('Atlantic Salmon Fillet', 'Beef Ribeye', 'Basmati Rice', 'Parmesan Cheese', 'Olive Oil')
)
SELECT 'Mock data insertion complete' AS status;