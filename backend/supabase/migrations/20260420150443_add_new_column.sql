ALTER TABLE menu_items
ADD COLUMN IF NOT EXISTS is_available boolean not null default true;

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS order_status  text not null default 'completed';
-- pending, completed, cancelled

ALTER TABLE menu_items
ADD COLUMN IF NOT EXISTS is_available boolean not null default true;

ALTER TABLE suppliers
ADD COLUMN IF NOT EXISTS contact_email text,
ADD COLUMN IF NOT EXISTS contact_phone text;

