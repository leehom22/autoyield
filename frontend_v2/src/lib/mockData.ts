
const now = Date.now();
const d = (daysAgo: number) => new Date(now - daysAgo * 86400000).toISOString();
const future = (days: number) => new Date(now + days * 86400000).toISOString();
let _oid = 100;

export const MOCK_INVENTORY = [
  { id: 'inv_001', name: 'Chicken Breast', qty: 45, unit_cost: 8.50, expiry_timestamp: future(2), min_stock_level: 20 },
  { id: 'inv_002', name: 'Jasmine Rice (25kg)', qty: 12, unit_cost: 32.00, expiry_timestamp: future(60), min_stock_level: 5 },
  { id: 'inv_003', name: 'Palm Cooking Oil', qty: 8, unit_cost: 14.20, expiry_timestamp: future(90), min_stock_level: 4 },
  { id: 'inv_004', name: 'Coconut Milk', qty: 3, unit_cost: 4.80, expiry_timestamp: future(1), min_stock_level: 10 },
  { id: 'inv_005', name: 'Sambal Belacan', qty: 18, unit_cost: 6.30, expiry_timestamp: future(30), min_stock_level: 8 },
  { id: 'inv_006', name: 'Pandan Leaves', qty: 2, unit_cost: 1.50, expiry_timestamp: future(1), min_stock_level: 5 },
  { id: 'inv_007', name: 'Eggs (tray 30)', qty: 6, unit_cost: 12.00, expiry_timestamp: future(10), min_stock_level: 3 },
  { id: 'inv_008', name: 'Dried Anchovies', qty: 15, unit_cost: 18.00, expiry_timestamp: future(45), min_stock_level: 5 },
  { id: 'inv_009', name: 'Tamarind Paste', qty: 9, unit_cost: 5.40, expiry_timestamp: future(120), min_stock_level: 3 },
  { id: 'inv_010', name: 'Fresh Prawns', qty: 4, unit_cost: 28.00, expiry_timestamp: future(1), min_stock_level: 6 },
];

export const MOCK_MENU = [
  { id: 'm1', name: 'Nasi Lemak Special', category: 'Rice', current_price: 12.90, margin_percent: 62, status: 'active' },
  { id: 'm2', name: 'Char Kuey Teow', category: 'Noodle', current_price: 10.50, margin_percent: 55, status: 'active' },
  { id: 'm3', name: 'Roti Canai', category: 'Bread', current_price: 3.50, margin_percent: 72, status: 'promo' },
  { id: 'm4', name: 'Laksa Penang', category: 'Noodle', current_price: 11.90, margin_percent: 48, status: 'active' },
  { id: 'm5', name: 'Nasi Goreng Kampung', category: 'Rice', current_price: 9.90, margin_percent: 58, status: 'active' },
  { id: 'm6', name: 'Teh Tarik', category: 'Beverage', current_price: 3.20, margin_percent: 80, status: 'active' },
  { id: 'm7', name: 'Milo Ais', category: 'Beverage', current_price: 4.50, margin_percent: 75, status: 'active' },
  { id: 'm8', name: 'Ayam Goreng Berempah', category: 'Main', current_price: 14.90, margin_percent: 45, status: 'hidden' },
];

export const MOCK_SUPPLIERS = [
  { id: 's1', name: 'Farm Fresh Sdn Bhd', reliability_score: 92, avg_lead_time: 4, pricing_tiers: { '<100kg': 8.5, '100-500kg': 7.8, '>500kg': 7.2 } },
  { id: 's2', name: 'Seri Murni Trading', reliability_score: 78, avg_lead_time: 8, pricing_tiers: { standard: 6.0, bulk: 5.2 } },
  { id: 's3', name: 'Ocean Harvest Seafood', reliability_score: 65, avg_lead_time: 12, pricing_tiers: { regular: 28.0, contract: 24.5 } },
  { id: 's4', name: 'KL Dry Goods Wholesale', reliability_score: 88, avg_lead_time: 6, pricing_tiers: { retail: 15.0, wholesale: 12.0 } },
];

export const MOCK_STAFF = [
  { id: 'st1', name: 'Chef Ahmad', role: 'head_chef', shift_start: '06:00', shift_end: '14:00', current_load: 85, max_capacity_score: 95 },
  { id: 'st2', name: 'Mei Lin', role: 'sous_chef', shift_start: '10:00', shift_end: '18:00', current_load: 72, max_capacity_score: 88 },
  { id: 'st3', name: 'Raj Kumar', role: 'waiter', shift_start: '11:00', shift_end: '19:00', current_load: 45, max_capacity_score: 70 },
  { id: 'st4', name: 'Siti Aminah', role: 'cashier', shift_start: '08:00', shift_end: '16:00', current_load: 30, max_capacity_score: 60 },
  { id: 'st5', name: 'Ah Kow', role: 'prep_cook', shift_start: '05:00', shift_end: '13:00', current_load: 90, max_capacity_score: 80 },
];

const DISHES = ['Nasi Lemak', 'Char Kuey Teow', 'Roti Canai', 'Laksa Penang', 'Nasi Goreng', 'Teh Tarik', 'Milo Ais'];
const SEGMENTS = ['dine-in', 'takeaway', 'delivery', 'grab', 'walk-in'];

export function generateMockOrder() {
  const items = Array.from({ length: 1 + Math.floor(Math.random() * 3) }, () => ({
    name: DISHES[Math.floor(Math.random() * DISHES.length)],
    price: +(5 + Math.random() * 12).toFixed(2),
  }));
  const revenue = items.reduce((s, i) => s + i.price, 0);
  return {
    id: `ord_${++_oid}`,
    items,
    total_revenue: +revenue.toFixed(2),
    total_margin: +(revenue * (0.3 + Math.random() * 0.4)).toFixed(2),
    timestamp: new Date().toISOString(),
    customer_segment: SEGMENTS[Math.floor(Math.random() * SEGMENTS.length)],
  };
}

export const MOCK_DECISIONS = [
  { id: 'dl1', timestamp: d(0.1), trigger_signal: 'PRICE_ANOMALY', resolution: 'P-Agent wins',
    p_agent_argument: 'Cooking oil price increased 18% in the last 24h. We should raise menu prices for fried items by 8% to maintain margin targets.',
    r_agent_argument: 'An 8% menu price increase risks losing 12% of price-sensitive customers. Counter-proposal: raise by 4% and reduce portion size by 5%.',
    action_taken: 'Raised Char Kuey Teow price from RM9.90 to RM10.50 (+6%). Nasi Goreng adjusted to RM9.90. Portion unchanged.' },
  { id: 'dl2', timestamp: d(0.3), trigger_signal: 'LOW_INVENTORY', resolution: 'Consensus',
    p_agent_argument: 'Coconut milk stock at 3 units, below min_stock_level of 10. Recommend immediate PO to Farm Fresh Sdn Bhd for 50 units.',
    r_agent_argument: 'Agree on urgency. However, suggest splitting order: 30 units from Farm Fresh (reliable) and 20 from Seri Murni (cheaper) to optimize cost.',
    action_taken: 'Created PO #1247 for 30 units coconut milk from Farm Fresh @ RM4.80/unit. PO #1248 for 20 units from Seri Murni @ RM4.20/unit.' },
  { id: 'dl3', timestamp: d(1), trigger_signal: 'DEMAND_SHIFT', resolution: 'R-Agent wins',
    p_agent_argument: 'Roti Canai demand up 35% this week. Recommend increasing price from RM3.00 to RM3.80 to capture value.',
    r_agent_argument: 'Roti Canai is a loss-leader that drives beverage sales (78% attach rate for Teh Tarik). Price increase would reduce traffic. Instead, run a combo deal.',
    action_taken: 'Created "Roti + Teh Tarik Combo" at RM5.90 (vs RM6.70 individual). Maintained base Roti Canai at RM3.50 promo price.' },
  { id: 'dl4', timestamp: d(2), trigger_signal: 'STAFF_OVERLOAD', resolution: 'Consensus',
    p_agent_argument: 'Prep cook Ah Kow at 90% load during morning shift. Risk of quality degradation and food safety issues.',
    r_agent_argument: 'Agree. Recommend shifting 2 prep tasks to sous chef Mei Lin (72% load) rather than hiring additional staff.',
    action_taken: 'Reassigned vegetable prep and sauce preparation to Mei Lin during 10:00-12:00. Ah Kow load reduced to 75%.' },
];

export const MOCK_NOTIFICATIONS = [
  { id: 'n1', priority: 'high', status: 'pending', message: 'Agent wants to auto-create PO #1249 for 50kg chicken breast from Farm Fresh at RM8.50/kg (total RM425). Current stock critically low at 5 units.',
    proposed_action: { type: 'create_po', supplier: 'Farm Fresh Sdn Bhd', item: 'Chicken Breast', qty: 50, unit_price: 8.5, total: 425 },
    created_at: new Date().toISOString() },
  { id: 'n2', priority: 'medium', status: 'pending', message: 'Agent proposes 12% price increase on Laksa Penang (RM11.90 → RM13.30) due to rising prawn costs.',
    proposed_action: { type: 'price_update', item: 'Laksa Penang', old_price: 11.9, new_price: 13.3, reason: 'prawn_cost_increase' },
    created_at: d(0.05) },
];

export const MOCK_WEEKLY_REPORT = {
  id: 'wr-final-001',
  timestamp: new Date().toISOString(),
  trigger_signal: 'WEEKLY_FORECAST',
  resolution: 'Strategic Consensus Reached',
  
  p_agent_argument: 
    "Revenue growth is robust at 12.4%, but our exposure to volatile seafood costs is at a critical 30-day high. " +
    "**Atlantic Salmon** unit costs have spiked by 15% due to logistics surcharges. " +
    "I recommend an immediate 8% price adjustment on premium mains to protect our net margins. " +
    "We must prioritize high-margin 'Beverage' upselling to offset the protein cost burn.",

  r_agent_argument: 
    "An 8% price hike on signature dishes like **Seabass Aglio Olio** risks a 15% drop in 'Regular' segment retention. " +
    "Our data shows sensitivity is high this month. " +
    "Counter-proposal: Maintain current pricing but implement a 'Smart Portion' strategy for garnish and sides. " +
    "We should secure a 90-day fixed-price contract with **Oceanic Seafood Supply** to hedge against further spikes.",

  action_taken: 
    "### 📊 Weekly Performance Summary\n\n" +
    "* **Total Revenue:** RM 24,850.00 (+12.4% WoW)\n" +
    "* **Net Margin:** 61.2% (Target: 60.0%)\n" +
    "* **Top Performer:** *Seabass Aglio Olio* (215 orders)\n" +
    "* **Critical Risk:** *Atlantic Salmon* stock level at 2.5 days buffer.\n\n" +
    "### ✅ Key Actions Executed\n\n" +
    "1. **Dynamic Pricing:** Adjusted *Grilled Salmon* price from RM42.00 to RM45.00 (+7%) to track unit cost surge.\n" +
    "2. **Procurement Lock:** Finalized emergency PO for 40kg *Sea Bass Whole* at RM22.11/unit.\n" +
    "3. **Ops Optimization:** Reassigned 2 staff from 'Bartender' to 'Line Cook' during Friday peak (19:00-21:00) to resolve prep bottlenecks.\n" +
    "4. **Marketing:** Launched a low-inventory-drain 'Tea Tarik' bundle to boost ticket size without straining meat stocks.\n\n" +
    "### 💡 Proactive Recommendations\n\n" +
    "- **Inventory:** Transition to local suppliers for 'Organic Mixed Vegetables' to reduce carbon-tax related surcharges.\n" +
    "- **Staffing:** Cross-train *Chen Hao* for KDS management as projected order velocity will exceed 2.5x next weekend.",
};

export const MOCK_SSE_STATE = {
  queue_length: 7,
  is_paused: false,
  simulated_time: new Date(2026, 3, 25, 14, 35, 0).toISOString(),
};

/* ── Macro Trends (P0) ── */
export const MOCK_MARKET_TRENDS = (() => {
  const records: { indicator: string; value: number; recorded_at: string }[] = [];
  for (let i = 29; i >= 0; i--) {
    const date = d(i);
    records.push({ indicator: 'oil_price', value: +(72 + Math.sin(i * 0.4) * 8 + Math.random() * 3).toFixed(2), recorded_at: date });
    records.push({ indicator: 'usd_myr', value: +(4.45 + Math.sin(i * 0.3) * 0.12 + Math.random() * 0.05).toFixed(4), recorded_at: date });
    records.push({ indicator: 'local_inflation', value: +(2.8 + Math.cos(i * 0.25) * 0.6 + Math.random() * 0.2).toFixed(2), recorded_at: date });
  }
  return records;
})();

/* ── Procurement Logs (P1) ── */
export const MOCK_PROCUREMENT_LOGS = [
  { id: 'pl1', ingredient_name: 'Chicken Breast', supplier_name: 'Farm Fresh Sdn Bhd', quantity: 50, unit_price: 8.50, status: 'delivered', estimated_arrival: d(-1), created_at: d(0.1) },
  { id: 'pl2', ingredient_name: 'Coconut Milk', supplier_name: 'Seri Murni Trading', quantity: 30, unit_price: 4.80, status: 'shipped', estimated_arrival: future(1), created_at: d(0.2) },
  { id: 'pl3', ingredient_name: 'Fresh Prawns', supplier_name: 'Ocean Harvest Seafood', quantity: 20, unit_price: 28.00, status: 'ordered', estimated_arrival: future(2), created_at: d(0.5) },
  { id: 'pl4', ingredient_name: 'Palm Cooking Oil', supplier_name: 'KL Dry Goods Wholesale', quantity: 10, unit_price: 14.20, status: 'pending', estimated_arrival: future(3), created_at: d(1) },
  { id: 'pl5', ingredient_name: 'Dried Anchovies', supplier_name: 'KL Dry Goods Wholesale', quantity: 15, unit_price: 18.00, status: 'cancelled', estimated_arrival: null, created_at: d(2) },
];

/* ── KDS Queue (P1) ── */
export const MOCK_KDS_QUEUE = [
  { id: 'kds1', order_id: 'ORD-201', table_number: '5', source: 'dine-in', items: [{ name: 'Nasi Lemak Special', quantity: 2 }, { name: 'Teh Tarik', quantity: 2 }], priority: 'urgent' as const, status: 'cooking', position_in_queue: 1, eta_minutes: 8, agent_note: 'VIP customer — prioritize quality', created_at: d(0) },
  { id: 'kds2', order_id: 'ORD-202', table_number: '12', source: 'dine-in', items: [{ name: 'Char Kuey Teow', quantity: 1 }, { name: 'Milo Ais', quantity: 1 }], priority: 'normal' as const, status: 'preparing', position_in_queue: 2, eta_minutes: 12, agent_note: null, created_at: d(0) },
  { id: 'kds3', order_id: 'ORD-203', table_number: null, source: 'grab', items: [{ name: 'Laksa Penang', quantity: 1 }, { name: 'Roti Canai', quantity: 3 }], priority: 'normal' as const, status: 'queued', position_in_queue: 3, eta_minutes: 18, agent_note: null, created_at: d(0) },
  { id: 'kds4', order_id: 'ORD-204', table_number: '3', source: 'dine-in', items: [{ name: 'Nasi Goreng Kampung', quantity: 2 }, { name: 'Ayam Goreng Berempah', quantity: 1 }, { name: 'Teh Tarik', quantity: 3 }], priority: 'normal' as const, status: 'queued', position_in_queue: 4, eta_minutes: 22, agent_note: 'Customer requested extra spicy', created_at: d(0) },
  { id: 'kds5', order_id: 'ORD-205', table_number: '8', source: 'walk-in', items: [{ name: 'Roti Canai', quantity: 1 }], priority: 'hold' as const, status: 'hold', position_in_queue: 5, eta_minutes: null, agent_note: 'Waiting for missing ingredient delivery', created_at: d(0) },
];

/* ── Knowledge Base (P2) ── */
export const MOCK_KNOWLEDGE_BASE = [
  { id: 'kb1', scenario_description: 'Cooking oil price spike of 18% triggered automatic menu price adjustment. Agent raised fried item prices by 6% instead of proposed 8%.', lesson_learned: 'Moderate price increases (5-7%) maintain customer retention better than aggressive adjustments. Combined with portion optimization, margin impact was minimized. Customer complaints remained below threshold.', performance_score: 0.87, created_at: d(0.5) },
  { id: 'kb2', scenario_description: 'Roti Canai demand surge (+35%) during weekend. Combo deal created instead of price increase to preserve loss-leader strategy.', lesson_learned: 'Loss-leader items with high attach rates (>70% beverage pairing) should not have price increases. Combo deals convert 34% of customers and increase average ticket by RM2.40.', performance_score: 0.93, created_at: d(1) },
  { id: 'kb3', scenario_description: 'Staff overload detected: prep cook at 90% capacity. Tasks reassigned to sous chef with 72% load.', lesson_learned: 'Cross-training staff enables dynamic load balancing without additional hiring costs. Quality scores maintained at 4.2/5 post-reassignment. Optimal load threshold is 80% — trigger alerts above this.', performance_score: 0.78, created_at: d(2) },
  { id: 'kb4', scenario_description: 'Supplier reliability drop: Ocean Harvest Seafood delivery delayed by 6 hours, impacting prawn-based menu items.', lesson_learned: 'Maintain backup supplier contracts for critical ingredients. Automatic menu item hiding when stock reaches 2-day buffer prevents customer disappointment. Revenue impact: -RM180 for 1 day.', performance_score: 0.62, created_at: d(4) },
  { id: 'kb5', scenario_description: 'Weekend peak hour analysis revealed beverage prep bottleneck between 12:00-13:00 causing 4-minute average delay.', lesson_learned: 'Pre-batching Teh Tarik base during 11:30-12:00 reduced beverage prep time by 40%. Customer wait time decreased from 12min to 8min average. Implement pre-batch protocol for top 3 beverages.', performance_score: 0.85, created_at: d(7) },
];

/* ── Supplier Contact Logs (P2) ── */
export const MOCK_SUPPLIER_CONTACT_LOGS = [
  { id: 'scl1', supplier_id: 's1', created_at: d(0.1), message_type: 'order', message_preview: 'PO #1249 — 50kg chicken breast at RM8.50/kg. Delivery by tomorrow 6AM.', quantity: 50, unit_price: 8.50, channel: 'whatsapp', status: 'sent' },
  { id: 'scl2', supplier_id: 's1', created_at: d(0.3), message_type: 'negotiation', message_preview: 'Requesting 5% volume discount for 30-day contract commitment.', quantity: null, unit_price: null, channel: 'whatsapp', status: 'received' },
  { id: 'scl3', supplier_id: 's1', created_at: d(1), message_type: 'inquiry', message_preview: 'Checking availability of organic free-range chicken. MOQ?', quantity: null, unit_price: null, channel: 'email', status: 'read' },
  { id: 'scl4', supplier_id: 's1', created_at: d(3), message_type: 'quote', message_preview: 'Updated price list for Q2 2026. Chicken +3%, Eggs stable.', quantity: null, unit_price: null, channel: 'email', status: 'received' },
  { id: 'scl5', supplier_id: 's2', created_at: d(0.2), message_type: 'order', message_preview: 'PO #1248 — 20 units coconut milk at RM4.20/unit.', quantity: 20, unit_price: 4.20, channel: 'whatsapp', status: 'sent' },
  { id: 'scl6', supplier_id: 's2', created_at: d(1), message_type: 'follow_up', message_preview: 'Following up on delayed shipment. ETA update needed.', quantity: null, unit_price: null, channel: 'phone', status: 'sent' },
  { id: 'scl7', supplier_id: 's3', created_at: d(0.5), message_type: 'complaint', message_preview: 'Last prawn delivery had 15% undersized. Quality control issue.', quantity: null, unit_price: null, channel: 'whatsapp', status: 'sent' },
  { id: 'scl8', supplier_id: 's4', created_at: d(0.1), message_type: 'order', message_preview: 'PO #1250 — Dried anchovies 15kg, cooking oil 10L. Standard pricing.', quantity: 25, unit_price: 16.50, channel: 'whatsapp', status: 'sent' },
];
