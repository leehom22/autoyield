-- ============================================================
-- MEX Agent — Supabase Schema
-- Run this entire file in your Supabase SQL Editor
-- ============================================================

-- 1. Inventory
create table if not exists inventory (
  id            uuid primary key default gen_random_uuid(),
  item_id       text unique not null,
  name          text not null,
  qty           numeric not null default 0,
  unit          text not null default 'kg',
  cost_per_unit numeric not null default 0,
  expiry_date   date,
  expiry_risk_score numeric default 0,   -- 0.0 to 1.0, computed or updated by agent
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

-- 2. Menu
create table if not exists menu (
  id          uuid primary key default gen_random_uuid(),
  item_id     text unique not null,
  name        text not null,
  price       numeric not null,
  cost        numeric not null,
  is_active   boolean default true,
  category    text,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

-- 3. Orders
create table if not exists orders (
  id            uuid primary key default gen_random_uuid(),
  order_id      text unique not null,
  items         jsonb not null,           -- [{ item_id, qty, price }]
  total_revenue numeric not null,
  status        text default 'pending',  -- pending | completed | cancelled
  created_at    timestamptz default now()
);

-- 4. Finance snapshot (daily)
create table if not exists finance_snapshots (
  id              uuid primary key default gen_random_uuid(),
  snapshot_date   date unique not null default current_date,
  daily_revenue   numeric default 0,
  current_margin_avg numeric default 0,
  burn_rate       numeric default 0,
  created_at      timestamptz default now()
);

-- 5. Staff / Ops
create table if not exists staff_roster (
  id            uuid primary key default gen_random_uuid(),
  staff_id      text unique not null,
  name          text not null,
  role          text not null,
  is_active     boolean default true,
  shift_start   time,
  shift_end     time,
  created_at    timestamptz default now()
);

-- 6. Suppliers
create table if not exists suppliers (
  id               uuid primary key default gen_random_uuid(),
  supplier_id      text unique not null,
  name             text not null,
  item_id          text references inventory(item_id),
  unit_cost        numeric not null,
  reliability_index numeric default 1.0,  -- 0.0 to 1.0
  logistics_fee    numeric default 0,
  estimated_delivery_hrs int default 24,
  created_at       timestamptz default now()
);

-- 7. Marketing campaigns
create table if not exists campaigns (
  id                   uuid primary key default gen_random_uuid(),
  campaign_id          text unique not null,
  strategy_type        text not null,     -- VOUCHER | FLASH_SALE | AD_BOOST
  config               jsonb not null,
  goal                 text not null,     -- clear_stock | maximize_margin
  status               text default 'active',
  estimated_reach      int,
  activation_timestamp timestamptz default now(),
  created_at           timestamptz default now()
);

-- 8. Agent decisions / audit log
create table if not exists agent_decisions (
  id               uuid primary key default gen_random_uuid(),
  event_id         text unique not null,
  decision_type    text not null,
  p_agent_logic    text,
  r_agent_logic    text,
  action_taken     jsonb,
  expected_outcome jsonb,
  actual_outcome   jsonb,
  lesson_learned   text,
  embedding_id     text,
  created_at       timestamptz default now()
);

-- 9. Notifications
create table if not exists notifications (
  id              uuid primary key default gen_random_uuid(),
  notification_id text unique not null,
  priority        text not null,          -- high | medium
  message         text not null,
  proposed_action jsonb,
  delivery_channel text default 'admin_dashboard',
  is_read         boolean default false,
  created_at      timestamptz default now()
);

-- ============================================================
-- Seed data — basic inventory and menu items to test with
-- ============================================================
insert into inventory (item_id, name, qty, unit, cost_per_unit, expiry_risk_score) values
  ('inv_salmon',   'Salmon',      5,  'kg',  85.0, 0.8),
  ('inv_seabass',  'Sea Bass',    20, 'kg',  45.0, 0.2),
  ('inv_rice',     'Rice',        15, 'kg',  3.5,  0.1),
  ('inv_noodle',   'Egg Noodle',  30, 'kg',  4.0,  0.1),
  ('inv_chicken',  'Chicken',     25, 'kg',  12.0, 0.4)
on conflict (item_id) do nothing;

insert into menu (item_id, name, price, cost, category) values
  ('menu_salmon_rice',   'Salmon Rice',     28.0, 12.0, 'mains'),
  ('menu_seabass_set',   'Sea Bass Set',    22.0, 8.0,  'mains'),
  ('menu_chicken_rice',  'Chicken Rice',    12.0, 4.5,  'mains'),
  ('menu_noodle_soup',   'Noodle Soup',     11.0, 3.5,  'mains')
on conflict (item_id) do nothing;

insert into finance_snapshots (snapshot_date, daily_revenue, current_margin_avg, burn_rate) values
  (current_date, 0, 0.58, 450)
on conflict (snapshot_date) do nothing;

insert into staff_roster (staff_id, name, role, shift_start, shift_end) values
  ('staff_001', 'Ahmad',   'chef',    '08:00', '17:00'),
  ('staff_002', 'Siti',    'chef',    '11:00', '20:00'),
  ('staff_003', 'Raju',    'cashier', '09:00', '18:00'),
  ('staff_004', 'Mei Ling','server',  '10:00', '19:00')
on conflict (staff_id) do nothing;

insert into suppliers (supplier_id, name, item_id, unit_cost, reliability_index, logistics_fee, estimated_delivery_hrs) values
  ('sup_001', 'FreshMarine Sdn Bhd',  'inv_salmon',  85.0, 0.92, 5.0,  4),
  ('sup_002', 'OceanKing Supplies',   'inv_salmon',  78.0, 0.75, 12.0, 8),
  ('sup_003', 'SeaBest Trading',      'inv_seabass', 42.0, 0.88, 6.0,  6),
  ('sup_004', 'GrainMaster Bhd',      'inv_rice',    3.2,  0.95, 2.0,  12)
on conflict (supplier_id) do nothing;