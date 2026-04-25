
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
  id: 'wr1', timestamp: d(1), trigger_signal: 'WEEKLY_FORECAST', resolution: 'Full consensus',
  p_agent_argument: 'Revenue up 8.2% WoW driven by combo promotions. Chicken and prawn costs trending upward. Recommend pre-purchasing 2-week inventory buffer for volatile items. Marketing spend ROI at 3.2x — suggest increasing weekend social media budget by 20%.',
  r_agent_argument: 'Agree on revenue trend. However, 2-week buffer ties up RM2,800 in working capital. Counter: 1-week buffer + negotiate fixed-price contracts with Farm Fresh. Marketing ROI calculation excludes customer acquisition cost — true ROI closer to 2.1x. Maintain current spend.',
  action_taken: `Weekly Performance Summary (Simulated Week 12)\n\n📊 Revenue: RM18,450 (+8.2% WoW)\n📈 Gross Margin: 58.3% (target: 55%)\n🛒 Orders: 847 total (avg RM21.80/order)\n⭐ Top Seller: Nasi Lemak Special (186 orders)\n📉 Underperformer: Ayam Goreng Berempah (12 orders — hidden from menu)\n\nKey Actions Taken:\n1. Adjusted 3 menu prices based on ingredient cost changes\n2. Created 4 purchase orders totaling RM1,680\n3. Reassigned 2 prep tasks to balance staff workload\n4. Launched Roti + Teh Tarik combo (conversion rate: 34%)\n\nRecommendations:\n- Lock in chicken price with Farm Fresh via 30-day contract\n- Consider reintroducing Ayam Goreng with revised recipe/pricing\n- Expand delivery partnerships (currently 18% of revenue)`,
};

export const MOCK_SSE_STATE = {
  queue_length: 7,
  is_paused: false,
  simulated_time: new Date(2026, 3, 25, 14, 35, 0).toISOString(),
};
