import { useState, useCallback, useRef, useEffect } from 'react';
import { adjustVelocity, triggerCrisis } from '../lib/api';
import { useToastStore } from '../store/toastStore';
import { supabase } from '../lib/supabase';
import { MOCK_INVENTORY } from '../lib/mockData';
import { ChevronDown, ChevronRight } from 'lucide-react';

export default function GodModeConsole() {
  const [velocity, setVelocity] = useState(1.0);
  const [invQty, setInvQty] = useState(1.0);
  const [invCost, setInvCost] = useState(1.0);
  const [oilPrice, setOilPrice] = useState(1.0);
  const [targetId, setTargetId] = useState('');
  const [exchangeRate, setExchangeRate] = useState<number | null>(4.2350);
  const [items, setItems] = useState<any[]>(MOCK_INVENTORY);
  const [itemMultipliers, setItemMultipliers] = useState<Record<string, { qty: number; cost: number }>>({});
  const [expandItems, setExpandItems] = useState(false);
  const addToast = useToastStore((s) => s.addToast);
  const addError = useToastStore((s) => s.addError);
  const dRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const debounced = useCallback((fn: () => void) => { clearTimeout(dRef.current); dRef.current = setTimeout(fn, 400); }, []);

  useEffect(() => {
    supabase.from('inventory').select('*').then(({ data }) => { if (data?.length) setItems(data); });
    supabase.from('market_trends_history')
    .select('value')
    .eq('indicator', 'usd_myr')
    .order('recorded_at', { ascending: false })
    .limit(1)
    .then(({ data }) => {
      if (data?.[0]) setExchangeRate(data[0].value);
    });
  }, []);

  const fire = async (label: string, fn: () => Promise<any>) => {
    try { await fn(); addToast('info', `${label} applied`); } catch (e: any) { addError(e.message); addToast('error', `Failed: ${label}`); }
  };

  const getItemMult = (id: string) => itemMultipliers[id] || { qty: 1, cost: 1 };
  const setItemMult = (id: string, field: 'qty' | 'cost', val: number) => {
    const m = { ...getItemMult(id), [field]: val };
    setItemMultipliers((prev) => ({ ...prev, [id]: m }));
    debounced(() => fire(`${id} ${field}`, () => triggerCrisis({
      inventory_target_id: id,
      ...(field === 'qty' ? { inventory_qty_multiplier: val } : { inventory_cost_multiplier: val }),
    })));
  };

  return (
    <div style={{ overflow: 'auto', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* Velocity */}
      <div className="panel panel-accent-cyan">
        <div className="panel-header"><h3>Order Velocity</h3><span className="badge badge-cyan mono">{velocity.toFixed(1)}x</span></div>
        <div className="panel-body">
          <input type="range" min={0.1} max={10} step={0.1} value={velocity} onChange={(e) => { const v = parseFloat(e.target.value); setVelocity(v); debounced(() => fire('Velocity', () => adjustVelocity(v))); }} />
          <div className="row" style={{ justifyContent: 'space-between', fontSize: 9, color: 'var(--text-2)', marginTop: 3 }}><span>0.1x</span><span>5x</span><span>10x</span></div>
        </div>
      </div>

      {/* Crisis — Global */}
      <div className="panel panel-accent-orange">
        <div className="panel-header"><h3>Crisis Injection (Global)</h3><span className="badge badge-orange">sandbox</span></div>
        <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div>
            <label style={{ display: 'block', fontSize: 10, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 3 }}>Target ID (blank = global)</label>
            <input type="text" value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="e.g. inv_001" style={{ maxWidth: 220 }} />
          </div>
          <Slider label="Inventory Qty Multiplier" value={invQty} onChange={(v) => { setInvQty(v); debounced(() => fire('Inv Qty', () => triggerCrisis({ inventory_qty_multiplier: v, ...(targetId ? { inventory_target_id: targetId } : {}) }))); }} />
          <Slider label="Inventory Cost Multiplier" value={invCost} onChange={(v) => { setInvCost(v); debounced(() => fire('Inv Cost', () => triggerCrisis({ inventory_cost_multiplier: v, ...(targetId ? { inventory_target_id: targetId } : {}) }))); }} />
          <Slider label="Oil Price Multiplier" value={oilPrice} onChange={(v) => { setOilPrice(v); debounced(() => fire('Oil', () => triggerCrisis({ oil_price_multiplier: v }))); }} />
        </div>
      </div>

      {/* Per-Item Inventory Controls */}
      <div className="panel">
        <div className="panel-header" style={{ cursor: 'pointer' }} onClick={() => setExpandItems(!expandItems)}>
          <h3>{expandItems ? <ChevronDown size={11} /> : <ChevronRight size={11} />} Per-Item Inventory Controls</h3>
          <span className="text-2" style={{ fontSize: 10 }}>{items.length} items</span>
        </div>
        {expandItems && (
          <div className="panel-body" style={{ padding: 0, maxHeight: 300 }}>
            <table className="data-table">
              <thead><tr><th>Item</th><th className="text-right">Qty</th><th className="text-right">Cost</th><th>Qty ×</th><th>Cost ×</th></tr></thead>
              <tbody>
                {items.map((item) => {
                  const m = getItemMult(item.id);
                  return (
                    <tr key={item.id}>
                      <td className="truncate" style={{ maxWidth: 100 }}>{item.name || item.id}</td>
                      <td className="text-right mono text-1">{item.qty}</td>
                      <td className="text-right mono text-1">${item.unit_cost}</td>
                      <td style={{ width: 100 }}>
                        <div className="row gap-4">
                          <input type="range" min={0} max={10} step={0.1} value={m.qty} onChange={(e) => setItemMult(item.id, 'qty', parseFloat(e.target.value))} style={{ flex: 1 }} />
                          <span className="mono text-cyan" style={{ fontSize: 9, width: 28, textAlign: 'right' }}>{m.qty.toFixed(1)}</span>
                        </div>
                      </td>
                      <td style={{ width: 100 }}>
                        <div className="row gap-4">
                          <input type="range" min={0} max={10} step={0.1} value={m.cost} onChange={(e) => setItemMult(item.id, 'cost', parseFloat(e.target.value))} style={{ flex: 1 }} />
                          <span className="mono text-orange" style={{ fontSize: 9, width: 28, textAlign: 'right' }}>{m.cost.toFixed(1)}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Exchange Rate */}
      <div className="panel panel-accent-purple">
        <div className="panel-header"><h3>Exchange Rate (USD/MYR)</h3><span className="badge badge-purple">read-only</span></div>
        <div className="panel-body row gap-8">
          <span className="text-1" style={{ fontSize: 11 }}>Current rate:</span>
          <span className="mono text-purple" style={{ fontSize: 16, fontWeight: 700 }}>{exchangeRate?.toFixed(4) ?? '—'}</span>
          <span className="text-2" style={{ fontSize: 10, marginLeft: 4 }}>Not yet active in backend</span>
        </div>
      </div>
    </div>
  );
}

function Slider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: 'var(--text-1)' }}>{label}</span>
        <span className="mono text-cyan" style={{ fontSize: 11 }}>{value.toFixed(1)}x</span>
      </div>
      <input type="range" min={0} max={10} step={0.1} value={value} onChange={(e) => onChange(parseFloat(e.target.value))} />
    </div>
  );
}
