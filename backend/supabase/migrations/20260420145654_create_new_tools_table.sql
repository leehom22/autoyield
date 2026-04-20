-- ============================================================
-- KDS (Kitchen Display System) table — run in Supabase SQL Editor
-- ============================================================

create table if not exists kds_queue (
    id                   uuid primary key default gen_random_uuid(),
    kds_entry_id         text unique not null,
    order_id             text not null,
    table_number         text,
    items                jsonb not null,
    priority             text not null default 'normal',    -- normal | urgent | hold
    status               text not null default 'displayed', -- displayed | queued | completed | cancelled
    estimated_prep_minutes int not null,
    eta_timestamp        timestamptz not null,
    position_in_queue    int not null default 1,
    agent_note           text,
    created_at           timestamptz default now(),
    completed_at         timestamptz
);

-- ============================================================
-- Supplier contact log — tracks every outbound message
-- ============================================================

create table if not exists supplier_contact_logs (
    id                   uuid primary key default gen_random_uuid(),
    contact_log_id       text unique not null,
    supplier_id          text not null,
    supplier_name        text not null,
    message_type         text not null,
    message_body         text not null,
    proposed_qty         numeric,
    proposed_unit_price  numeric,
    channel_used         text not null default 'logged_only',
    status               text not null default 'sent',
    created_at           timestamptz default now()
);

-- ============================================================
-- Festival calendar — Malaysian public holidays + food impact
-- ============================================================

create table if not exists festival_calendar (
    id             uuid primary key default gen_random_uuid(),
    name           text not null,
    event_date     date not null,
    type           text not null,   -- public_holiday | religious | cultural
    demand_impact  text,            -- free text e.g. "+40% noodles during CNY"
    staffing_note  text,
    country        text default 'MY',
    created_at     timestamptz default now()
);

-- Seed Malaysian festivals 2025-2026
insert into festival_calendar (name, event_date, type, demand_impact, staffing_note) values
    ('Chinese New Year',          '2026-01-29', 'cultural',       '+50% noodle dishes, +30% overall dinner covers', 'Non-Muslim staff may request leave'),
    ('Chinese New Year Day 2',    '2026-01-30', 'public_holiday', '+40% family set meals, reduced lunch walk-ins',  NULL),
    ('Thaipusam',                 '2026-02-17', 'religious',      'Moderate impact, +15% vegetarian options',       'Hindu staff may request leave'),
    ('Hari Raya Aidilfitri Day 1','2026-03-20', 'religious',      '-70% lunch covers, +80% pre-Raya dinner week',   'Muslim staff on leave, reduced ops'),
    ('Hari Raya Aidilfitri Day 2','2026-03-21', 'public_holiday', '-70% covers, many outlets closed',               'Skeleton crew only'),
    ('Labour Day',                '2026-05-01', 'public_holiday', '+20% lunch covers, normal dinner',               NULL),
    ('Wesak Day',                 '2026-05-12', 'religious',      '+20% vegetarian demand',                         'Buddhist staff may request leave'),
    ('Hari Raya Aidiladha',       '2026-06-28', 'religious',      '-40% Muslim customer base, normal for others',   'Muslim staff on leave'),
    ('National Day',              '2026-08-31', 'public_holiday', '+25% dinner covers, family dining surge',        NULL),
    ('Malaysia Day',              '2026-09-16', 'public_holiday', '+20% covers',                                    NULL),
    ('Deepavali',                 '2026-10-18', 'cultural',       '+30% Indian cuisine demand, +15% overall',       'Hindu staff may request leave'),
    ('Christmas Day',             '2026-12-25', 'cultural',       '+40% dinner covers, set menu demand spikes',     NULL),
    ('Ramadan Start (est.)',       '2026-03-01', 'religious',      '-60% lunch covers, +90% Iftar dinner 6-8pm',    'Adjust lunch staffing, boost dinner crew')
on conflict do nothing;