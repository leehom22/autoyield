CREATE OR REPLACE FUNCTION reset_all_data()
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- 1. Disable FK checks
    SET session_replication_role = replica;

    -- 2. Clear all tables
    TRUNCATE TABLE 
        supplier_contact_logs,
        procurement_logs,
        inventory_pricing_history,
        kds_queue,
        orders,
        decision_logs,
        notifications,
        marketing_campaigns,
        knowledge_base,
        staff_roster,
        menu_items,
        inventory,
        suppliers,
        festival_calendar,
        market_trends_history
    CASCADE;

    -- 3. Insert data (same as your original)

    -- 3.1 Suppliers
    INSERT INTO suppliers (id, name, categories, reliability_score, avg_lead_time, min_order_qty, pricing_tiers, contact_email, contact_phone) VALUES
        ('c11eda48-accf-4898-893c-2958a3ef8bde', 'Oceanic Seafood Supply', ARRAY['Seafood'], 0.95, 12, 20, '{"1-50": 28.5, "201+": 24.0, "51-200": 26.0}'::JSONB, 'user_8939a606@example.com', '+60119545634'),
        ('03704ec1-3ec0-43bb-99f9-fa25b20aa148', 'Prime Meat Co.', ARRAY['Meat'], 0.92, 18, 15, '{"1-30": 42.0, "101+": 36.5, "31-100": 39.0}'::JSONB, 'user_dd08388e@example.com', '+60153399955'),
        ('a758c995-6e51-44b8-b9d5-00dd1f7d7a1a', 'Green Valley Produce', ARRAY['Vegetables'], 0.88, 10, 10, '{"1-50": 4.2, "201+": 3.6, "51-200": 3.9}'::JSONB, 'user_582c2707@example.com', '+60176554594'),
        ('0e115802-e769-4b3f-94aa-368801ce2b0a', 'Global Grains & Dry', ARRAY['Dry Goods'], 0.97, 24, 50, '{"501+": 2.0, "1-100": 2.5, "101-500": 2.2}'::JSONB, 'user_071b855d@example.com', '+60113308075'),
        ('307a628a-68e0-42ac-93a8-b0173545ec9a', 'DairyPure Malaysia', ARRAY['Dairy'], 0.90, 8, 20, '{"1-40": 6.5, "151+": 5.4, "41-150": 5.9}'::JSONB, 'user_f9dddfdf@example.com', '+60141053405'),
        ('edab964c-14cf-45de-8da0-b5033e44e970', 'BevX Beverages', ARRAY['Beverages'], 0.99, 6, 100, '{"1-200": 0.6, "1001+": 0.5, "201-1000": 0.55}'::JSONB, 'user_0b8364ff@example.com', '+60132129408'),
        ('5d89dfef-57cc-43fb-8898-f083d686f736', 'Local Artisan Dairy', ARRAY['Dairy','Dessert'], 0.85, 5, 5, '{"1-20": 15.0, "21-50": 14.0}'::JSONB, 'user_9d6673a4@example.com', '+60177410514'),
        ('b46acbb1-e01d-437e-aba6-cfcb5fab07bf', 'Premium Oil & Spice', ARRAY['Dry Goods'], 0.94, 14, 12, '{"81+": 8.2, "1-30": 9.5, "31-80": 8.8}'::JSONB, 'user_5c039ede@example.com', '+60140237257');

    -- 3.2 Inventory
    INSERT INTO inventory (id, name, qty, unit, unit_cost, base_price, current_price, expiry_timestamp, min_stock_level, category, version, created_at) VALUES
        ('a35730d2-5186-44e0-b7ce-2ec1a0d2ea4f', 'Fresh Milk', 32, 'L', 1.2, 2.5, 2.3, '2026-04-21T10:35:51.158437+00:00', 15, 'Dairy', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('e54f47de-ce13-4c6d-a893-e1cd3b4b1e59', 'Olive Oil (Extra Virgin)', 28, 'L', 9.5, 18.0, 17.0, '2026-07-07T10:35:51.158437+00:00', 8, 'Dry Goods', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('249396a0-726c-4a8d-9440-3826bcf32294', 'Flour (All Purpose)', 85, 'kg', 0.9, 1.8, 1.7, '2026-07-27T10:35:51.158437+00:00', 20, 'Dry Goods', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('8a6cec1d-4536-4627-8686-c1f023336838', 'Basmati Rice', 162.8, 'kg', 2.5, 4.5, 4.2, '2026-06-02T10:35:51.158437+00:00', 30, 'Dry Goods', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('d74bb6f1-9dfb-451a-b8ff-ad11d4c12c50', 'Craft Beer (IPA)', 24, 'pcs', 2.2, 5.0, 4.8, '2026-05-13T10:35:51.158437+00:00', 40, 'Beverages', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('8580c292-d747-409a-9918-4445beff04ca', 'Beef Ribeye', 0, 'kg', 42.0, 68.0, 65.0, '2026-04-21T10:35:51.158437+00:00', 6, 'Meat', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('ae324b66-9b6d-4307-9922-9b86c506a6f8', 'Black Tiger Prawns', 28.8, 'kg', 35.0, 55.0, 52.0, '2026-04-22T10:35:51.158437+00:00', 8, 'Seafood', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('13de006f-a8ae-4998-9065-c8f7d3400a6d', 'Unsalted Butter', 19.2, 'kg', 6.5, 12.0, 11.5, '2026-04-28T10:35:51.158437+00:00', 8, 'Dairy', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('4a23fa19-cae6-48b8-8632-51f1aa17cdd2', 'Sea Bass Whole', 0, 'kg', 22.0, 38.0, 38.0, '2026-04-23T10:35:51.158437+00:00', 5, 'Seafood', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('fc9fb361-153e-46ea-afc2-cc0a0e8577dd', 'Spaghetti Pasta', 56.5, 'kg', 1.8, 3.2, 3.0, '2026-05-18T10:35:51.158437+00:00', 20, 'Dry Goods', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('1f0afc3f-712f-47f8-9030-d153a496d3cd', 'Garlic', 19.045, 'kg', 4.0, 7.0, 6.5, '2026-04-30T10:35:51.158437+00:00', 5, 'Vegetables', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('99603fe0-c224-4ed2-b0c0-e0735838262f', 'Coca-Cola (Can)', 230, 'pcs', 0.6, 1.5, 1.5, '2026-06-17T10:35:51.158437+00:00', 100, 'Beverages', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('93ddc07f-4310-4b48-8dda-7b3ed0f18ca3', 'Atlantic Salmon Fillet', 21.5, 'kg', 28.5, 45.0, 42.0, '2026-04-20T10:35:51.158437+00:00', 10, 'Seafood', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('609fad25-d438-42c4-9eed-668d568b067d', 'Chicken Breast', 80.4, 'kg', 8.5, 15.0, 14.5, '2026-04-26T10:35:51.158437+00:00', 15, 'Meat', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('1417c15e-8932-47a6-987a-d042f28f63a7', 'Heirloom Tomatoes', 25.95, 'kg', 5.8, 9.9, 9.5, '2026-04-20T10:35:51.158437+00:00', 10, 'Vegetables', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('3ae8350f-60e2-4314-baa7-3a2cab372af2', 'Vanilla Ice Cream', 3.75, 'L', 4.0, 7.5, 7.0, '2026-05-02T10:35:51.158437+00:00', 5, 'Dessert', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('99272bc8-ceee-43e3-9a77-a722ed080680', 'Lamb Chop', 0, 'kg', 38.0, 60.0, 58.0, '2026-04-20T10:35:51.158437+00:00', 4, 'Meat', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('c6c747ff-a7ed-4562-bd6b-a8c6b51dd7d0', 'Organic Mixed Vegetables', 58.45, 'kg', 4.2, 7.5, 7.2, '2026-04-19T10:35:51.158437+00:00', 20, 'Vegetables', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('f11a7ad1-57f1-4eec-9f34-12301e9ed21e', 'Lemon Juice', 11.25, 'L', 3.0, 5.5, 5.0, '2026-04-23T10:35:51.158437+00:00', 5, 'Beverages', 0, '2026-04-18T10:35:51.158437+00:00'),
        ('d45ed325-92f8-4c8a-95e4-2a283f00e8e5', 'Parmesan Cheese', 0, 'kg', 15.0, 28.0, 26.0, '2026-04-24T10:35:51.158437+00:00', 3, 'Dairy', 0, '2026-04-18T10:35:51.158437+00:00');

    -- 3.3 Menu items
    INSERT INTO menu_items (id, name, ingredients, base_price, current_price, margin_percent, status, category, created_at, is_available) VALUES
        ('f0111396-7098-40e4-a4dd-f75e7b455744', 'Grilled Salmon', '[{"qty":0.2,"item_name":"Atlantic Salmon Fillet"}]'::JSONB, 45.0, 42.0, 86.43, 'active', 'Main', '2026-04-18T10:35:51.158437+00:00', true),
        ('9ec83a01-9a8a-4438-b0d3-af2e58bed7b7', 'Seabass Aglio Olio', '[{"qty":0.25,"item_name":"Sea Bass Whole"},{"qty":0.15,"item_name":"Spaghetti Pasta"},{"qty":0.02,"item_name":"Olive Oil"},{"qty":0.01,"item_name":"Garlic"}]'::JSONB, 38.0, 36.0, 80.0, 'active', 'Main', '2026-04-18T10:35:51.158437+00:00', true),
        ('45f5c13e-5212-4adc-9085-b0e06e107366', 'Garlic Butter Prawns', '[{"qty":0.15,"item_name":"Black Tiger Prawns"},{"qty":0.03,"item_name":"Unsalted Butter"},{"qty":0.01,"item_name":"Garlic"}]'::JSONB, 55.0, 52.0, 83.65, 'active', 'Main', '2026-04-18T10:35:51.158437+00:00', true),
        ('91a42e77-81cc-4f98-bcfe-4099511a1ceb', 'Chicken Parmigiana', '[{"qty":0.2,"item_name":"Chicken Breast"},{"qty":0.05,"item_name":"Parmesan Cheese"},{"qty":0.02,"item_name":"Flour"}]'::JSONB, 18.5, 17.9, 82.12, 'active', 'Main', '2026-04-18T10:35:51.158437+00:00', true),
        ('6acc589e-7a3a-4e4d-a464-41cb3ae0ab3f', 'Ribeye Steak', '[{"qty":0.3,"item_name":"Beef Ribeye"},{"qty":0.02,"item_name":"Unsalted Butter"},{"qty":0.01,"item_name":"Garlic"}]'::JSONB, 68.0, 65.0, 80.62, 'active', 'Main', '2026-04-18T10:35:51.158437+00:00', true),
        ('89ec06a8-2629-4afe-9519-84e3983c5045', 'Lamb Chop with Veg', '[{"qty":0.25,"item_name":"Lamb Chop"},{"qty":0.15,"item_name":"Organic Mixed Vegetables"}]'::JSONB, 60.0, 58.0, 83.62, 'active', 'Main', '2026-04-18T10:35:51.158437+00:00', true),
        ('011ce68f-e5c3-4816-a5c8-66c575ca07ae', 'Garden Fresh Salad', '[{"qty":0.1,"item_name":"Organic Mixed Vegetables"},{"qty":0.05,"item_name":"Heirloom Tomatoes"}]'::JSONB, 9.9, 9.5, 87.37, 'active', 'Appetizer', '2026-04-18T10:35:51.158437+00:00', true),
        ('3de35ace-a23a-4f74-91f1-013c1558dff8', 'Tomato Bruschetta', '[{"qty":0.08,"item_name":"Heirloom Tomatoes"},{"qty":0.01,"item_name":"Olive Oil"},{"qty":0.005,"item_name":"Garlic"}]'::JSONB, 8.5, 8.0, 82.5, 'active', 'Appetizer', '2026-04-18T10:35:51.158437+00:00', true),
        ('648d28df-a736-47d0-ba76-06c8e2ffeaa7', 'Cheese Platter', '[{"qty":0.1,"item_name":"Parmesan Cheese"}]'::JSONB, 14.0, 13.5, 84.44, 'active', 'Appetizer', '2026-04-18T10:35:51.158437+00:00', true),
        ('34bb872b-5d0e-4660-a0be-4f5648843dfa', 'Butter Garlic Rice', '[{"qty":0.2,"item_name":"Basmati Rice"},{"qty":0.02,"item_name":"Unsalted Butter"}]'::JSONB, 5.0, 4.8, 81.25, 'active', 'Side', '2026-04-18T10:35:51.158437+00:00', true),
        ('490bd64f-3514-4a7e-b61d-9f6c1e61376b', 'French Fries', '[{"qty":0.15,"item_name":"Organic Mixed Vegetables"}]'::JSONB, 6.5, 6.2, 79.03, 'active', 'Side', '2026-04-18T10:35:51.158437+00:00', true),
        ('102edb92-228d-464b-ab9d-c7b9147d12fb', 'Coke (Can)', '[{"qty":1,"item_name":"Coca-Cola (Can)"}]'::JSONB, 1.5, 1.5, 40.0, 'active', 'Beverage', '2026-04-18T10:35:51.158437+00:00', true),
        ('30b03aef-65e1-414a-b312-f4922bfd6a11', 'Craft Beer', '[{"qty":1,"item_name":"Craft Beer (IPA)"}]'::JSONB, 5.0, 4.8, 72.92, 'active', 'Beverage', '2026-04-18T10:35:51.158437+00:00', true),
        ('a4679552-dfad-4ed4-b454-b95ca19600d3', 'Lemonade', '[{"qty":0.05,"item_name":"Lemon Juice"}]'::JSONB, 4.5, 4.2, 64.29, 'active', 'Beverage', '2026-04-18T10:35:51.158437+00:00', true),
        ('818f0560-7cf1-406e-829e-b7fae21cb501', 'Vanilla Ice Cream Cup', '[{"qty":0.15,"item_name":"Vanilla Ice Cream"}]'::JSONB, 7.5, 7.0, 80.0, 'active', 'Dessert', '2026-04-18T10:35:51.158437+00:00', true);

    -- 3.4 Staff roster
    INSERT INTO staff_roster (id, name, role, hourly_rate, shift_start, shift_end, max_capacity_score, current_load) VALUES
        ('0760c26f-b01d-4710-af0e-6498b5fa6454', 'James Wong', 'Head Chef', 35.0, '2026-04-18T00:00:00+00:00', '2026-04-18T12:00:00+00:00', 0.95, 0.70),
        ('4db9850a-aaad-41c4-9b65-a6b0e0284808', 'Sarah Lim', 'Sous Chef', 28.0, '2026-04-18T04:00:00+00:00', '2026-04-18T14:00:00+00:00', 0.90, 0.60),
        ('03a0daa0-c927-49c0-8f6d-1bea5fd97735', 'Ahmad Faiz', 'Line Cook', 18.0, '2026-04-18T01:00:00+00:00', '2026-04-18T09:00:00+00:00', 0.80, 0.85),
        ('189a7174-f2bb-49db-a03a-e63e5f7c94de', 'Mei Ling', 'Pastry Chef', 22.0, '2026-04-17T23:00:00+00:00', '2026-04-18T07:00:00+00:00', 0.85, 0.50),
        ('74610524-e198-472c-92fe-4952794c4731', 'Raj Kumar', 'Kitchen Helper', 12.0, '2026-04-18T02:00:00+00:00', '2026-04-18T11:00:00+00:00', 0.75, 0.90),
        ('c020d0f9-cc3e-4de0-9cdb-03bc1ad89cb8', 'Tan Wei', 'Service Manager', 30.0, '2026-04-18T03:00:00+00:00', '2026-04-18T15:00:00+00:00', 0.92, 0.40),
        ('11f9e91d-8a76-4244-9294-5299138a3855', 'Lisa Ng', 'Bartender', 16.0, '2026-04-18T09:00:00+00:00', '2026-04-18T18:00:00+00:00', 0.88, 0.65),
        ('6da471db-7e7b-4ad6-ad5c-d0c0011ed6a5', 'Kumar S', 'Dishwasher', 10.0, '2026-04-18T06:00:00+00:00', '2026-04-18T14:00:00+00:00', 0.70, 0.80),
        ('2e648992-e6c6-4ad8-b186-54b0b8c73555', 'Priya K', 'Server', 8.5, '2026-04-18T03:00:00+00:00', '2026-04-18T12:00:00+00:00', 0.82, 0.75),
        ('71192aa3-e00a-4963-a094-18ebb8923aeb', 'Chen Hao', 'Server', 8.5, '2026-04-18T09:00:00+00:00', '2026-04-18T17:00:00+00:00', 0.82, 0.60);

    -- 3.5 Market trends
    INSERT INTO market_trends_history (id, indicator, value, recorded_at) VALUES
        ('eafeb734-724f-4492-97d0-994dbb646a54', 'oil_price', 82.5, '2026-04-11T10:35:51.158437+00:00'),
        ('79d66150-d430-4e23-ae85-89b011f48dff', 'oil_price', 83.1, '2026-04-12T10:35:51.158437+00:00'),
        ('b1540a54-5a81-4a65-9711-9c86fb741e98', 'oil_price', 83.8, '2026-04-13T10:35:51.158437+00:00'),
        ('f3cf3877-05f0-40b4-91e3-31426a742421', 'oil_price', 84.2, '2026-04-14T10:35:51.158437+00:00'),
        ('b2760a6d-3e5d-4864-a49c-b33f89aa044c', 'oil_price', 84.9, '2026-04-15T10:35:51.158437+00:00'),
        ('32303777-7b53-4835-9f1a-d41f4aaacd23', 'oil_price', 85.1, '2026-04-16T10:35:51.158437+00:00'),
        ('ec3e315a-4f3d-4d77-94eb-c0b9b9ccb93d', 'oil_price', 85.4, '2026-04-17T10:35:51.158437+00:00'),
        ('56baeadf-f258-4e9a-a271-b423015b6e79', 'oil_price', 85.4, '2026-04-18T10:35:51.158437+00:00'),
        ('ffbf10b9-14d5-4bac-9286-1670f41b5aa5', 'usd_myr', 4.68, '2026-04-11T10:35:51.158437+00:00'),
        ('562bd2c1-183c-449e-af03-2c834ca1bcfa', 'usd_myr', 4.69, '2026-04-12T10:35:51.158437+00:00'),
        ('c459977d-17a5-48c1-885d-7fd19b63ac45', 'usd_myr', 4.7, '2026-04-13T10:35:51.158437+00:00'),
        ('a36f1f97-b794-41ea-bd6f-845a3dbc16aa', 'usd_myr', 4.7, '2026-04-14T10:35:51.158437+00:00'),
        ('4c1d7f0f-3bc7-4c36-ad9c-a60b8fb9f56e', 'usd_myr', 4.71, '2026-04-15T10:35:51.158437+00:00'),
        ('57023bf1-ae40-441e-8e6e-858f704022e4', 'usd_myr', 4.72, '2026-04-16T10:35:51.158437+00:00'),
        ('c88bfec8-9b20-44f8-9585-4ad5a60d05e0', 'usd_myr', 4.72, '2026-04-17T10:35:51.158437+00:00'),
        ('675f5af4-1186-49de-982a-b1de7e33bba7', 'usd_myr', 4.72, '2026-04-18T10:35:51.158437+00:00'),
        ('427bf647-ac4c-4e96-a409-e2b9af4e1993', 'local_inflation', 2.6, '2026-03-19T10:35:51.158437+00:00'),
        ('0c599ca3-13e9-413c-a4f3-fdea864103dc', 'local_inflation', 2.7, '2026-03-29T10:35:51.158437+00:00'),
        ('1df5f9c5-72ea-4efa-a2e4-c81d3073a7df', 'local_inflation', 2.8, '2026-04-08T10:35:51.158437+00:00'),
        ('d1bfe248-a499-4417-b42c-9bb1f1657802', 'local_inflation', 2.8, '2026-04-18T10:35:51.158437+00:00');

    -- 3.6 Orders (sample)
    INSERT INTO orders (id, items, total_revenue, total_margin, timestamp, customer_segment, order_status) VALUES
        ('9c1be1f1-36f0-4e54-bd64-d1e1fa7a5fde', '[{"id":"011ce68f-e5c3-4816-a5c8-66c575ca07ae","name":"Garden Fresh Salad","price":9.5}]', 9.5, 8.3, '2026-04-20T08:30:00+00:00', 'Regular', 'completed'),
        ('5eaf5309-2724-4b28-835f-55fd66683426', '[{"id":"818f0560-7cf1-406e-829e-b7fae21cb501","name":"Vanilla Ice Cream Cup","price":7.0},{"id":"648d28df-a736-47d0-ba76-06c8e2ffeaa7","name":"Cheese Platter","price":13.5}]', 20.5, 17.0, '2026-04-20T08:30:00+00:00', 'Regular', 'completed'),
        ('0cf2936c-faf5-495e-bbfd-3017679ed26f', '[{"id":"45f5c13e-5212-4adc-9085-b0e06e107366","name":"Garlic Butter Prawns","price":52.0},{"id":"9ec83a01-9a8a-4438-b0d3-af2e58bed7b7","name":"Seabass Aglio Olio","price":36.0},{"id":"6acc589e-7a3a-4e4d-a464-41cb3ae0ab3f","name":"Ribeye Steak","price":65.0}]', 153.0, 124.7, '2026-04-20T09:00:00+00:00', 'Regular', 'completed'),
        ('dacc3edc-e95e-4168-9312-69affa74fa37', '[{"id":"011ce68f-e5c3-4816-a5c8-66c575ca07ae","name":"Garden Fresh Salad","price":9.5},{"id":"89ec06a8-2629-4afe-9519-84e3983c5045","name":"Lamb Chop with Veg","price":58.0}]', 67.5, 56.8, '2026-04-20T10:00:00+00:00', 'Regular', 'completed'),
        ('22a1ddab-d039-4fce-9ef0-6eea4cf033ba', '[{"id":"45f5c13e-5212-4adc-9085-b0e06e107366","name":"Garlic Butter Prawns","price":52.0},{"id":"a4679552-dfad-4ed4-b454-b95ca19600d3","name":"Lemonade","price":4.2},{"id":"34bb872b-5d0e-4660-a0be-4f5648843dfa","name":"Butter Garlic Rice","price":4.8}]', 61.0, 50.1, '2026-04-20T11:00:00+00:00', 'New', 'completed'),
        ('67b9fd50-58a9-4d14-b0c9-fa8ecd0d8ecb', '[{"id":"648d28df-a736-47d0-ba76-06c8e2ffeaa7","name":"Cheese Platter","price":13.5}]', 13.5, 11.4, '2026-04-20T12:00:00+00:00', 'New', 'completed'),
        ('542924d9-7c09-41db-a402-4bf9176b49c5', '[{"id":"818f0560-7cf1-406e-829e-b7fae21cb501","name":"Vanilla Ice Cream Cup","price":7.0},{"id":"3de35ace-a23a-4f74-91f1-013c1558dff8","name":"Tomato Bruschetta","price":8.0}]', 15.0, 12.2, '2026-04-20T12:30:00+00:00', 'ChurnRisk', 'completed'),
        ('5d1b0e0a-a1fb-4dab-b84d-0a379c5624a3', '[{"id":"91a42e77-81cc-4f98-bcfe-4099511a1ceb","name":"Chicken Parmigiana","price":17.9},{"id":"102edb92-228d-464b-ab9d-c7b9147d12fb","name":"Coke (Can)","price":1.5},{"id":"648d28df-a736-47d0-ba76-06c8e2ffeaa7","name":"Cheese Platter","price":13.5}]', 32.9, 26.7, '2026-04-20T13:00:00+00:00', 'Regular', 'completed'),
        ('7bf6d9c0-9f4e-4faa-8a70-0ccdc87ac19d', '[{"id":"818f0560-7cf1-406e-829e-b7fae21cb501","name":"Vanilla Ice Cream Cup","price":7.0},{"id":"3de35ace-a23a-4f74-91f1-013c1558dff8","name":"Tomato Bruschetta","price":8.0},{"id":"45f5c13e-5212-4adc-9085-b0e06e107366","name":"Garlic Butter Prawns","price":52.0}]', 67.0, 55.7, '2026-04-20T13:30:00+00:00', 'Regular', 'completed'),
        ('ec7067e9-2b1e-4f63-8142-c1c168872697', '[{"id":"f0111396-7098-40e4-a4dd-f75e7b455744","name":"Grilled Salmon","price":42.0}]', 42.0, 36.3, '2026-04-20T14:00:00+00:00', 'Regular', 'completed');

    -- 3.7 Decision logs
    INSERT INTO decision_logs (id, timestamp, trigger_signal, p_agent_argument, r_agent_argument, resolution, action_taken) VALUES
        ('e546fa79-2c1f-44e8-b5ad-d37496905bf7', '2026-04-20T08:00:00+00:00', 'INVENTORY_ADJUST', 'Normal restock — no price anomaly detected. Invoice price RM87/kg is only 2.35% above stored cost RM85/kg, well within 20% threshold.', 'Price within 20% of stored cost — safe to accept. Adding 10kg to existing 11.5kg = 21.5kg total.', 'Consensus Reached', 'INVENTORY_ADJUST - 93ddc07f-4310-4b48-8dda-7b3ed0f18ca3'),
        ('cbde943a-84ea-414b-8ec8-c66e775eaa8e', '2026-04-20T08:00:00+00:00', 'INVENTORY_ADJUST', 'Normal restock — no price anomaly detected. Invoice price RM13.50/kg is 12.5% above stored cost RM12.00/kg, within 20% threshold.', 'Price within 20% of stored cost — safe to accept. Adding 15kg delivery to existing 50.4kg stock.', 'Consensus Reached', 'INVENTORY_ADJUST - 609fad25-d438-42c4-9eed-668d568b067d'),
        ('69ccc44b-5c03-4910-acc2-e909fd005fce', '2026-04-20T08:00:00+00:00', 'INVENTORY_ADJUST', 'Normal restock — no price anomaly detected. Invoice price RM13.50/kg is 12.5% above stored cost RM12.00/kg, within the 20% threshold.', 'Price within 20% of stored cost — safe to accept. Adding 15kg delivery to existing 65.4kg stock = 80.4kg total.', 'Consensus Reached', 'INVENTORY_ADJUST - 609fad25-d438-42c4-9eed-668d568b067d');

    -- 3.8 Notifications
    INSERT INTO notifications (id, notification_id, priority, message, proposed_action, status, created_at, is_read) VALUES
        ('6b6f5a36-57d9-4c97-ae20-77bbe09fea4d', '45932176-ba99-47dc-bb01-a284c1438764', 'high', 'REQUEST: Run 20% discount on Seabass Aglio Olio (only noodle dish) this Friday.\n\n⚠️ BLOCKERS IDENTIFIED:\n1. Sea Bass is OUT OF STOCK — emergency restock ordered from best supplier (RM22.11/unit, 99% reliability, 6hr delivery)\n2. Kitchen CANNOT handle projected surge — need 28 additional staff for 30 extra orders. Current load 67.5% with medium shortage risk.\n3. Yield simulation shows margin drops 80%→75%, requiring 33% volume increase to break even. Recommendation: MAINTAIN price.\n\nRISK OF INACTION: Missed Friday revenue opportunity.\nRISK OF ACTION: Kitchen overload, stockout mid-promotion, potential profit loss if volume doesn\'t increase 33%.\n\nPlease approve or suggest modifications (e.g., smaller discount, limited hours, or add temp staff).', '{"day":"Friday","item":"Seabass Aglio Olio","action":"FLASH_SALE","item_id":"9ec83a01-9a8a-4438-b0d3-af2e58bed7b7","discount":0.2,"new_price":28.8,"current_price":36.0,"restock_ordered":true,"capacity_feasible":false,"margin_after_discount":"75%"}'::JSONB, 'pending', '2026-04-23T03:00:54.517718+00:00', false),
        ('355a9761-2c57-481e-94dc-a5c75f29d6e6', '6fffe653-f430-4df1-ab85-0486ea7a949c', 'high', 'REQUEST: Run 20% discount on Seabass Aglio Olio (only noodle dish) this Friday.\n\n⚠️ BLOCKERS IDENTIFIED:\n1. Sea Bass is OUT OF STOCK — emergency restock ordered from best supplier (RM22.11/unit, 99% reliability, 6hr delivery)\n2. Kitchen CANNOT handle projected surge — need 28 additional staff for 30 extra orders. Current load 67.5% with medium shortage risk.\n3. Yield simulation shows margin drops 80%→75%, requiring 33% volume increase to break even. Recommendation: MAINTAIN price.\n\nRISK OF INACTION: Missed Friday revenue opportunity.\nRISK OF ACTION: Kitchen overload, stockout mid-promotion, potential profit loss if volume doesn\'t increase 33%.\n\nPlease approve or suggest modifications (e.g., smaller discount, limited hours, or add temp staff).', '{"day":"Friday","item":"Seabass Aglio Olio","action":"FLASH_SALE","item_id":"9ec83a01-9a8a-4438-b0d3-af2e58bed7b7","discount":0.2,"new_price":28.8,"current_price":36.0,"restock_ordered":true,"capacity_feasible":false,"margin_after_discount":"75%"}'::JSONB, 'pending', '2026-04-23T03:02:27.849009+00:00', false),
        ('59bb4a0b-f3fe-446e-aca6-4aae592ede05', 'f21ed0aa-19fd-4c2e-8829-40cc6e60ae97', 'high', 'USER REQUEST: I want to run a 20% discount promotion on all noodle dishes this Friday.\n\nCONSENSUS REACHED:\nP-Agent: A blanket 20% discount on noodle dishes is a profit-killer. The numbers are unequivocal: every dish loses RM 1.90–RM 7.20 per unit, margins drop 3–5 percentage points, and you\'d need a 30–33% volume surge just to break even — but with an elasticity of only -1.2, demand won\'t stretch that far. Recommend rejecting the blanket discount and instead targeting specific dishes or a smaller discount (10–12%).', '{"decision":"I want to run a 20% discount promotion on all noodle dishes this Friday."}'::JSONB, 'pending', '2026-04-23T14:00:17.961589+00:00', false);

    -- 3.9 KDS queue
    INSERT INTO kds_queue (id, kds_entry_id, order_id, table_number, items, priority, status, estimated_prep_minutes, eta_timestamp, position_in_queue, agent_note, created_at, completed_at) VALUES
        ('fa1e4396-0cc0-486a-909f-fb1014ab9639', 'kds_8a0475c2', 'SURGE-ALERT-001', 'ALL', '[{"qty":1,"menu_item_id":"011ce68f-e5c3-4816-a5c8-66c575ca07ae","menu_item_name":"Garden Fresh Salad","special_instructions":"PRIORITY ITEM — push for all new orders, fast prep"},{"qty":1,"menu_item_id":"3de35ace-a23a-4f74-91f1-013c1558dff8","menu_item_name":"Tomato Bruschetta","special_instructions":"PRIORITY ITEM — push for all new orders, fast prep"},{"qty":1,"menu_item_id":"490bd64f-3514-4a7e-b61d-9f6c1e61376b","menu_item_name":"French Fries","special_instructions":"PRIORITY ITEM — push for all new orders, fast prep"}]', 'urgent', 'displayed', 18, '2026-04-24T17:21:21.137169+00:00', 1, 'SURGE 92% LOAD. Pull Ribeye/Seabass/Lamb/ChkParm/CheesePlate. Conserve rice — suggest noodle/fries upsell.', '2026-04-24T17:03:21.765514+00:00', NULL);

    -- 3.10 Knowledge base
    INSERT INTO knowledge_base (id, embedding_vector, scenario_description, lesson_learned, performance_score, created_at) VALUES
        ('53bbd9a7-bb3b-4db6-97f4-c224443f7c6c', '[0]'::vector, 'Event be2f6f7d-c4e6-4d45-a0fa-d6f2828146fa yielded revenue 0.0.', 'Adjust weights towards P-Agent if revenue drop > 15%.', 0.85, '2026-04-20T08:00:00+00:00'),
        ('8592c5b7-9fd9-4319-81a0-e01f9b5bb3a6', '[0]'::vector, 'Event 0e400710-b12d-4f74-9ffe-001de93df9bd yielded revenue 0.0.', 'Adjust weights towards P-Agent if revenue drop > 15%.', 0.85, '2026-04-20T08:00:00+00:00');

    -- 3.11 Supplier contact logs
    INSERT INTO supplier_contact_logs (id, contact_log_id, supplier_id, supplier_name, message_type, message_body, proposed_qty, proposed_unit_price, channel_used, status, created_at) VALUES
        ('6e262846-3166-46d2-99b9-0596d13c43c3', 'clog_1fa30892', 'edab964c-14cf-45de-8da0-b5033e44e970', 'BevX Beverages', 'emergency_restock', 'URGENT: Need Sea Bass Whole restocked before Friday for a planned promotion. Require minimum 30 units. Current stock is ZERO. Please deliver within 6 hours if possible. Price ceiling: RM 23.00/unit.', 30.0, 22.11, 'logged_only', 'sent', '2026-04-23T03:00:54.425275+00:00'),
        ('782b0780-9633-49ab-9d8a-d480be235af6', 'clog_187d3d25', 'edab964c-14cf-45de-8da0-b5033e44e970', 'BevX Beverages', 'emergency_restock', 'URGENT: Need Sea Bass Whole restocked before Friday for a planned promotion. Require minimum 30 units. Current stock is ZERO. Please deliver within 6 hours if possible. Price ceiling: RM 23.00/unit.', 30.0, 22.11, 'logged_only', 'sent', '2026-04-23T03:02:27.670955+00:00');

    -- 3.12 Marketing campaigns
    INSERT INTO marketing_campaigns (id, type, trigger_event, spend, revenue_uplift, active_status, roi_actual) VALUES
        ('0b98f3b5-d943-420f-83cf-900f67ec0b2d', 'VOUCHER', 'inventory_low_salmon', 120.0, 450.0, true, 2.75),
        ('2ed886c1-1070-41fb-b1db-94879cb248d3', 'FLASH_SALE', 'expiry_risk_cheese', 80.0, 320.0, true, 3.0),
        ('984483ea-61ec-4a48-a5c1-78cefa7a5263', 'AD_BOOST', 'weekend_surge', 200.0, 890.0, true, 3.45),
        ('31bb2649-af1a-4f72-89b3-fddbf99313e9', 'BUNDLE', 'new_menu_launch', 150.0, 610.0, false, NULL),
        ('cb10ec66-89d1-4af9-8726-9353bdcacb12', 'VOUCHER', 'churn_risk_segment', 90.0, 280.0, true, 2.11),
        ('23d68592-cc2b-49d4-a770-da93949973ce', 'FLASH_SALE', 'clear_stock', 50.0, NULL, true, NULL),
        ('fb3438cd-0036-408d-94e8-cde2c07b1cda', 'FLASH_SALE', 'clear_stock', 40.0, NULL, true, NULL),
        ('617ecf66-8eb0-4d69-a4da-96d1f0d2859b', 'FLASH_SALE', 'clear_stock', 50.0, NULL, true, NULL),
        ('e3aa95c1-2e05-49da-b3d8-4ebd3b05a691', 'FLASH_SALE', 'clear_stock', 50.0, NULL, true, NULL);

    -- 3.13 Festival calendar
    INSERT INTO festival_calendar (id, name, event_date, type, demand_impact, staffing_note, country, created_at) VALUES
        ('43e2fb06-cc5b-4987-8468-b6cdc09411c4', 'Chinese New Year', '2026-01-29', 'cultural', '+50% noodle dishes, +30% overall dinner covers', 'Non-Muslim staff may request leave', 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('29d53e0b-f536-474a-82a5-a734bbabe36a', 'Chinese New Year Day 2', '2026-01-30', 'public_holiday', '+40% family set meals, reduced lunch walk-ins', NULL, 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('63bf9312-3c1e-4dc1-bf62-70922ae36a98', 'Thaipusam', '2026-02-17', 'religious', 'Moderate impact, +15% vegetarian options', 'Hindu staff may request leave', 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('b12cd0dc-e1b2-4615-a867-b939a59828ee', 'Hari Raya Aidilfitri Day 1', '2026-03-20', 'religious', '-70% lunch covers, +80% pre-Raya dinner week', 'Muslim staff on leave, reduced ops', 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('d2627e77-9809-40a7-98f9-87a0ca2438f5', 'Hari Raya Aidilfitri Day 2', '2026-03-21', 'public_holiday', '-70% covers, many outlets closed', 'Skeleton crew only', 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('1969fe29-dcc3-4ada-bb91-9932356081de', 'Labour Day', '2026-05-01', 'public_holiday', '+20% lunch covers, normal dinner', NULL, 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('b7bdf1d4-e85c-4585-a182-11fbdadf6ce7', 'Wesak Day', '2026-05-12', 'religious', '+20% vegetarian demand', 'Buddhist staff may request leave', 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('238784ae-54dc-49bc-af1d-52a2be3fff99', 'Hari Raya Aidiladha', '2026-06-28', 'religious', '-40% Muslim customer base, normal for others', 'Muslim staff on leave', 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('80f71a28-0c3a-4014-acd4-2ce1855435fb', 'National Day', '2026-08-31', 'public_holiday', '+25% dinner covers, family dining surge', NULL, 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('275d79ff-4e59-47f5-80c9-3042bb9cac4a', 'Malaysia Day', '2026-09-16', 'public_holiday', '+20% covers', NULL, 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('b2a97fd6-88c5-428e-a9da-0924fd1945f0', 'Deepavali', '2026-10-18', 'cultural', '+30% Indian cuisine demand, +15% overall', 'Hindu staff may request leave', 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('45f1ee65-9fb5-4791-8d92-e742c3fc91ef', 'Christmas Day', '2026-12-25', 'cultural', '+40% dinner covers, set menu demand spikes', NULL, 'MY', '2026-04-20T15:00:52.642513+00:00'),
        ('70abdee8-e976-47d4-a684-8b3f8b11a669', 'Ramadan Start (est.)', '2026-03-01', 'religious', '-60% lunch covers, +90% Iftar dinner 6-8pm', 'Adjust lunch staffing, boost dinner crew', 'MY', '2026-04-20T15:00:52.642513+00:00');

    -- 3.14 Inventory pricing history
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
    WHERE name IN ('Atlantic Salmon Fillet', 'Beef Ribeye', 'Basmati Rice', 'Parmesan Cheese', 'Olive Oil');

    -- 3.15 Procurement logs
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
    WHERE random() < 0.4
    LIMIT 25;

    -- 4. Re‑enable FK checks
    SET session_replication_role = default;

    RETURN 'Database reset to snapshot from db_export.json (excluding agent_permissions).';
END;
$$;