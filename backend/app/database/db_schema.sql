-- ======================================================
-- AUTO-YIELD: FINAL DATABASE SCHEMA (Agent-Optimized)
-- ======================================================
-- Run this script in Supabase SQL editor.
-- It drops and recreates all tables with improvements.
-- Designed for LLM Agent autonomy + operational integrity.

-- Extensions (unchanged)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ======================================================
-- 1. Core Operations Domain
-- ======================================================

-- Inventory: added version column for optimistic lock
DROP TABLE IF EXISTS inventory CASCADE;
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    qty FLOAT DEFAULT 0.0,
    unit TEXT,
    unit_cost DECIMAL(12, 2),
    base_price DECIMAL(12, 2),
    current_price DECIMAL(12, 2),
    expiry_timestamp TIMESTAMPTZ,
    min_stock_level FLOAT DEFAULT 0.0,
    category TEXT,
    version INT DEFAULT 0,               -- optimistic lock for concurrent updates
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Menu Items: ingredients as JSONB (single atomic update)
DROP TABLE IF EXISTS menu_items CASCADE;
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    ingredients JSONB,                   -- [{"item_id": "...", "qty": 0.2}]
    base_price DECIMAL(12, 2),
    current_price DECIMAL(12, 2),
    margin_percent FLOAT,
    status TEXT CHECK (status IN ('active', 'hidden', 'promo')),
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orders (unchanged)
DROP TABLE IF EXISTS orders CASCADE;
-- add order_date
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    items JSONB,
    total_revenue DECIMAL(12, 2),
    total_margin DECIMAL(12, 2),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    customer_segment TEXT
);

-- ======================================================
-- 2. Supply Chain & Procurement Domain
-- ======================================================

DROP TABLE IF EXISTS suppliers CASCADE;
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    categories TEXT[],
    reliability_score FLOAT CHECK (reliability_score >= 0 AND reliability_score <= 1),
    avg_lead_time FLOAT,
    min_order_qty FLOAT,
    pricing_tiers JSONB
);

DROP TABLE IF EXISTS procurement_logs CASCADE;
CREATE TABLE procurement_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES inventory(id) ON DELETE RESTRICT,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE RESTRICT,
    qty FLOAT,
    unit_cost DECIMAL(12, 2),
    delivery_status TEXT,
    arrival_estimate TIMESTAMPTZ
);

-- ======================================================
-- 3. Human Capital & Capacity Domain (precise timestamps)
-- ======================================================

DROP TABLE IF EXISTS staff_roster CASCADE;
CREATE TABLE staff_roster (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    role TEXT,
    hourly_rate DECIMAL(12, 2),
    shift_start TIMESTAMPTZ,              -- exact start time
    shift_end TIMESTAMPTZ,                -- exact end time (can cross midnight)
    max_capacity_score FLOAT,
    current_load FLOAT DEFAULT 0.0
);

-- ======================================================
-- 4. Macro Environment Domain (historical + trend view)
-- ======================================================

-- Historical table for all market indicators
DROP TABLE IF EXISTS market_trends_history CASCADE;
CREATE TABLE market_trends_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator TEXT NOT NULL,              -- 'oil_price', 'usd_myr', 'local_inflation'
    value FLOAT NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- View that provides current value + calculated trend_slope (for Agent perception)
CREATE OR REPLACE VIEW market_trends_current AS
WITH ranked AS (
    SELECT 
        indicator,
        value,
        recorded_at,
        LAG(value) OVER (PARTITION BY indicator ORDER BY recorded_at) AS prev_value,
        ROW_NUMBER() OVER (PARTITION BY indicator ORDER BY recorded_at DESC) AS rn
    FROM market_trends_history
)
SELECT 
    indicator,
    value AS current_value,
    CASE 
        WHEN prev_value IS NULL THEN 0
        ELSE (value - prev_value)
    END AS trend_slope,
    recorded_at AS last_updated
FROM ranked
WHERE rn = 1;

-- ======================================================
-- 5. Marketing & Yield Domain (unchanged)
-- ======================================================

DROP TABLE IF EXISTS marketing_campaigns CASCADE;
CREATE TABLE marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT,
    trigger_event TEXT,
    spend DECIMAL(12, 2),
    revenue_uplift DECIMAL(12, 2),
    active_status BOOLEAN DEFAULT FALSE,
    roi_actual FLOAT
);

-- ======================================================
-- 6. Cognitive & Memory Domain
-- ======================================================

DROP TABLE IF EXISTS decision_logs CASCADE;
CREATE TABLE decision_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    trigger_signal TEXT,
    p_agent_argument TEXT,
    r_agent_argument TEXT,
    resolution TEXT,
    action_taken TEXT
);

DROP TABLE IF EXISTS knowledge_base CASCADE;
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    embedding_vector vector(1536),
    scenario_description TEXT,
    lesson_learned TEXT,
    performance_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================
-- 7. Inventory Pricing History (optional but recommended)
-- ======================================================

CREATE TABLE inventory_pricing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inventory_id UUID NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    unit_cost DECIMAL(12, 2),
    current_price DECIMAL(12, 2),
    effective_from TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================
-- 8. Indexes (performance)
-- ======================================================

CREATE INDEX idx_inventory_expiry ON inventory(expiry_timestamp);
CREATE INDEX idx_orders_timestamp ON orders(timestamp);
CREATE INDEX idx_menu_status ON menu_items(status);
CREATE INDEX idx_procurement_arrival ON procurement_logs(arrival_estimate);
CREATE INDEX idx_decision_timestamp ON decision_logs(timestamp);
CREATE INDEX idx_market_indicator_time ON market_trends_history(indicator, recorded_at);
CREATE INDEX idx_inventory_pricing_history_inventory_id ON inventory_pricing_history(inventory_id);

-- Vector index for RAG (IVFFlat, cosine distance)
CREATE INDEX idx_knowledge_embedding ON knowledge_base
  USING ivfflat (embedding_vector vector_cosine_ops)
  WITH (lists = 100);

-- ======================================================
-- 9. Row Level Security (RLS)
-- ======================================================

-- Enable RLS on all business tables
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE procurement_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_roster ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_trends_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketing_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE decision_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_pricing_history ENABLE ROW LEVEL SECURITY;

-- Manager: full access on all tables
CREATE POLICY manager_all_inventory ON inventory USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_menu_items ON menu_items USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_orders ON orders USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_suppliers ON suppliers USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_procurement_logs ON procurement_logs USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_staff_roster ON staff_roster USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_market_trends ON market_trends_history USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_marketing_campaigns ON marketing_campaigns USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_decision_logs ON decision_logs USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_knowledge_base ON knowledge_base USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY manager_all_inventory_pricing_history ON inventory_pricing_history USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');

-- Staff: read-only on most tables
CREATE POLICY staff_select_inventory ON inventory FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');
CREATE POLICY staff_select_menu_items ON menu_items FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');
CREATE POLICY staff_select_orders ON orders FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');
CREATE POLICY staff_select_procurement_logs ON procurement_logs FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');
CREATE POLICY staff_select_staff_roster ON staff_roster FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');
CREATE POLICY staff_select_market_trends ON market_trends_history FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');
CREATE POLICY staff_select_marketing_campaigns ON marketing_campaigns FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');


-- ======================================================
-- 10. Notification
-- ======================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_id TEXT NOT NULL,
    priority TEXT CHECK (priority IN ('high', 'medium')),
    message TEXT NOT NULL,
    proposed_action JSONB,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE
);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY manager_all_notifications ON notifications USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'manager');
CREATE POLICY staff_select_notifications ON notifications FOR SELECT USING (current_setting('request.jwt.claims', true)::json->>'user_role' = 'staff');


-- ======================================================
-- 11. Agent Permission
-- ======================================================

CREATE TABLE IF NOT EXISTS agent_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    allow_auto_price_update BOOLEAN DEFAULT TRUE,
    allow_auto_po_creation BOOLEAN DEFAULT TRUE,
    allow_auto_inventory_adjust BOOLEAN DEFAULT TRUE,
    allow_auto_marketing_campaign BOOLEAN DEFAULT FALSE,
    max_price_change_percent FLOAT DEFAULT 15.0,
    max_spend_amount DECIMAL(12,2) DEFAULT 500.00,
    max_discount_percent FLOAT DEFAULT 30.0,
    approval_mode_for_price_change TEXT DEFAULT 'require_approval',
    approval_mode_for_po TEXT DEFAULT 'require_approval',
    approval_mode_for_campaign TEXT DEFAULT 'require_approval',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT DEFAULT 'system'
);

INSERT INTO agent_permissions (id)
SELECT uuid_generate_v4()
WHERE NOT EXISTS (SELECT 1 FROM agent_permissions);


-- ======================================================
-- Refinement
-- ======================================================

-- Fill up inventory pricing history fields
ALTER TABLE inventory_pricing_history 
ADD COLUMN IF NOT EXISTS current_price DECIMAL(10,2);

-- Create Vector Similarity Query RPC for generate_post_mortem_learning
CREATE OR REPLACE FUNCTION match_knowledge_base (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  scenario_description text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    kb.id,
    kb.scenario_description,
    1 - (kb.embedding_vector <=> query_embedding) AS similarity
  FROM knowledge_base kb
  WHERE 1 - (kb.embedding_vector <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;