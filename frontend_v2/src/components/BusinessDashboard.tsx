import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { MOCK_INVENTORY, MOCK_MENU, MOCK_SUPPLIERS, MOCK_STAFF } from '../lib/mockData';
import { AlertTriangle, Package, UtensilsCrossed, Truck, Users } from 'lucide-react';

export default function BusinessDashboard() {
  const [inv, setInv] = useState<any[]>(MOCK_INVENTORY);
  const [menu, setMenu] = useState<any[]>(MOCK_MENU);
  const [supp, setSupp] = useState<any[]>(MOCK_SUPPLIERS);
  const [staff, setStaff] = useState<any[]>(MOCK_STAFF);
  const [tab, setTab] = useState<'inv' | 'menu' | 'supp' | 'staff'>('inv');

  useEffect(() => {
    const s = [
      supabase.channel('i2').on('postgres_changes', { event: '*', schema: 'public', table: 'inventory' }, () => fi()).subscribe(),
      supabase.channel('m2').on('postgres_changes', { event: '*', schema: 'public', table: 'menu_items' }, () => fm()).subscribe(),
      supabase.channel('s2').on('postgres_changes', { event: '*', schema: 'public', table: 'suppliers' }, () => fs()).subscribe(),
      supabase.channel('t2').on('postgres_changes', { event: '*', schema: 'public', table: 'staff_roster' }, () => ft()).subscribe(),
    ];
    fi(); fm(); fs(); ft();
    return () => { s.forEach((x) => supabase.removeChannel(x)); };
  }, []);
  const fi = async () => { const { data } = await supabase.from('inventory').select('*'); if (data?.length) setInv(data); };
  const fm = async () => { const { data } = await supabase.from('menu_items').select('*'); if (data?.length) setMenu(data); };
  const fs = async () => { const { data } = await supabase.from('suppliers').select('*'); if (data?.length) setSupp(data); };
  const ft = async () => { const { data } = await supabase.from('staff_roster').select('*'); if (data?.length) setStaff(data); };

  const dte = (ts: string | null) => { if (!ts) return null; return Math.max(0, Math.floor((new Date(ts).getTime() - Date.now()) / 86400000)); };
  const lowStockCount = inv.filter((i) => i.qty <= (i.min_stock_level ?? 0)).length;
  const expiringCount = inv.filter((i) => { const d = dte(i.expiry_timestamp); return d !== null && d <= 3; }).length;
  const avgMargin = menu.length ? (menu.reduce((s, m) => s + (m.margin_percent || 0), 0) / menu.length).toFixed(1) : '—';
  const avgLoad = staff.length ? Math.round(staff.reduce((s, x) => s + (x.current_load || 0), 0) / staff.length) : 0;

  const tabs: { key: typeof tab; icon: any; label: string; count: number }[] = [
    { key: 'inv', icon: Package, label: 'Inventory', count: inv.length },
    { key: 'menu', icon: UtensilsCrossed, label: 'Menu', count: menu.length },
    { key: 'supp', icon: Truck, label: 'Suppliers', count: supp.length },
    { key: 'staff', icon: Users, label: 'Staff', count: staff.length },
  ];

  return (
    <div className="flex-col" style={{ height: '100%' }}>
      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, padding: '10px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div className="stat-card"><span className="sc-label">Inventory Items</span><span className="sc-value text-cyan">{inv.length}</span></div>
        <div className="stat-card"><span className="sc-label">Low Stock / Expiring</span><span className="sc-value"><span className="text-orange">{lowStockCount}</span> <span className="text-2" style={{ fontSize: 12 }}>/</span> <span className="text-red">{expiringCount}</span></span></div>
        <div className="stat-card"><span className="sc-label">Avg Menu Margin</span><span className="sc-value text-green">{avgMargin}%</span></div>
        <div className="stat-card"><span className="sc-label">Avg Staff Load</span><span className="sc-value" style={{ color: avgLoad > 80 ? 'var(--orange)' : 'var(--green)' }}>{avgLoad}%</span></div>
      </div>

      {/* Tabs */}
      <div className="row" style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)', flexShrink: 0, padding: '0 6px' }}>
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding: '7px 12px', background: 'none', border: 'none',
            borderBottom: tab === t.key ? '2px solid var(--cyan)' : '2px solid transparent',
            color: tab === t.key ? 'var(--text-0)' : 'var(--text-2)',
            cursor: 'pointer', fontSize: 11, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 5, transition: 'all var(--ts)',
          }}>
            <t.icon size={12} />{t.label}
            <span style={{ fontSize: 9, background: 'var(--bg-active)', padding: '0 5px', borderRadius: 3 }}>{t.count}</span>
          </button>
        ))}
      </div>

      {/* Tables */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {tab === 'inv' && <table className="data-table"><thead><tr><th>Item</th><th className="text-right">Qty</th><th className="text-right">Cost</th><th className="text-right">Min</th><th className="text-right">Expiry</th><th className="text-right">Days</th><th>Risk</th></tr></thead><tbody>
          {inv.map((i) => { const d = dte(i.expiry_timestamp); const ls = i.qty <= (i.min_stock_level ?? 0); const er = d !== null && d <= 3; return (
            <tr key={i.id}><td className="truncate" style={{ maxWidth: 130 }}>{i.name || i.id}</td><td className="text-right mono">{i.qty}</td><td className="text-right mono">${i.unit_cost}</td><td className="text-right mono text-2">{i.min_stock_level ?? '—'}</td><td className="text-right mono text-2" style={{ fontSize: 10 }}>{i.expiry_timestamp ? new Date(i.expiry_timestamp).toLocaleDateString() : '—'}</td><td className="text-right mono" style={{ color: er ? 'var(--red)' : 'var(--text-1)' }}>{d !== null ? `${d}d` : '—'}</td>
              <td>{er && <span className="badge badge-red"><AlertTriangle size={9} /> Expiry</span>}{ls && <span className="badge badge-orange" style={{ marginLeft: er ? 3 : 0 }}>Low</span>}{!er && !ls && <span className="badge badge-green">OK</span>}</td></tr>); })}
        </tbody></table>}

        {tab === 'menu' && <table className="data-table"><thead><tr><th>Name</th><th>Category</th><th className="text-right">Price</th><th className="text-right">Margin</th><th>Status</th></tr></thead><tbody>
          {menu.map((m) => <tr key={m.id}><td>{m.name}</td><td className="text-2">{m.category}</td><td className="text-right mono">${m.current_price}</td><td className="text-right mono">{m.margin_percent}%</td><td><span className={`badge ${m.status === 'active' ? 'badge-green' : m.status === 'promo' ? 'badge-cyan' : 'badge-orange'}`}>{m.status}</span></td></tr>)}
        </tbody></table>}

        {tab === 'supp' && <table className="data-table"><thead><tr><th>Name</th><th className="text-right">Reliability</th><th className="text-right">Lead Time</th><th>Pricing Tiers</th></tr></thead><tbody>
          {supp.map((s) => <tr key={s.id}><td>{s.name}</td><td className="text-right"><span className={`mono ${s.reliability_score >= 80 ? 'text-green' : s.reliability_score >= 50 ? 'text-orange' : 'text-red'}`}>{s.reliability_score}</span></td><td className="text-right mono">{s.avg_lead_time}h</td><td className="text-2 truncate" style={{ maxWidth: 200, fontSize: 10 }}>{typeof s.pricing_tiers === 'object' ? JSON.stringify(s.pricing_tiers) : s.pricing_tiers}</td></tr>)}
        </tbody></table>}

        {tab === 'staff' && <table className="data-table"><thead><tr><th>Name</th><th>Role</th><th>Shift</th><th className="text-right">Load</th><th className="text-right">Capacity</th></tr></thead><tbody>
          {staff.map((s) => <tr key={s.id}><td>{s.name}</td><td><span className="badge badge-purple">{s.role}</span></td><td className="mono text-2" style={{ fontSize: 10 }}>{s.shift_start} – {s.shift_end}</td><td className="text-right"><span className={`mono ${(s.current_load ?? 0) > 80 ? 'text-orange' : 'text-green'}`}>{s.current_load}%</span></td><td className="text-right mono text-2">{s.max_capacity_score}</td></tr>)}
        </tbody></table>}
      </div>
    </div>
  );
}
