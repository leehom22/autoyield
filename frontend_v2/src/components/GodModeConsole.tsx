import { useState, useCallback, useRef, useEffect } from 'react';
import { adjustVelocity, triggerCrisis } from '../lib/api';
import { useToastStore } from '../store/toastStore';
import { supabase } from '../lib/supabase';
import { MOCK_INVENTORY } from '../lib/mockData';
import { ChevronDown, ChevronRight, Zap } from 'lucide-react';

// --- 内部封装：弹簧滑块组件 ---
function SpringSlider({ 
  label, 
  onApply, 
  accentColor = 'var(--cyan)' 
}: { 
  label: string; 
  onApply: (v: number) => void;
  accentColor?: string;
}) {
  const [val, setVal] = useState(1.0);
  const sliderRef = useRef<HTMLInputElement>(null);

  const handleReset = () => {
    // 只有在数值改变后才触发
    if (val !== 1.0) {
      onApply(val);
      // 强制触发回位
      setVal(1.0);
    }
  };

  return (
    <div style={{ marginBottom: 12 }}>
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: 'var(--text-1)' }}>{label}</span>
        <span className="mono" style={{ 
          fontSize: 11, 
          color: val === 1.0 ? 'var(--text-2)' : accentColor,
          fontWeight: 600 
        }}>
          {val.toFixed(1)}x
        </span>
      </div>
      <input 
        ref={sliderRef}
        type="range" min={0.1} max={3.0} step={0.1} 
        value={val} 
        onChange={(e) => setVal(parseFloat(e.target.value))}
        // 关键点：无论点击还是长距离拖拽，只要鼠标/手指松开，一定会触发
        onPointerUp={handleReset}
        onKeyUp={handleReset} // 兼容键盘操作
        style={{ width: '100%', accentColor: accentColor }}
      />
    </div>
  );
}

// --- Main component ---
export default function GodModeConsole() {
  const [velocity, setVelocity] = useState(1.0);
  const [targetId, setTargetId] = useState('');
  const [exchangeRate, setExchangeRate] = useState<number | null>(4.2350);
  const [items, setItems] = useState<any[]>(MOCK_INVENTORY);
  const [expandItems, setExpandItems] = useState(false);
  
  const addToast = useToastStore((s) => s.addToast);
  const addError = useToastStore((s) => s.addError);
  const dRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const debounced = useCallback((fn: () => void) => {
    clearTimeout(dRef.current);
    dRef.current = setTimeout(fn, 400);
  }, []);

  useEffect(() => {
    supabase.from('inventory').select('*').then(({ data }) => { if (data?.length) setItems(data); });
    supabase.from('market_trends_history').select('value').eq('indicator', 'usd_myr')
      .order('recorded_at', { ascending: false }).limit(1)
      .then(({ data }) => { if (data?.[0]) setExchangeRate(data[0].value); });
  }, []);

  const fire = async (label: string, fn: () => Promise<any>) => {
    try { await fn(); addToast('info', `${label} applied`); } 
    catch (e: any) { addError(e.message); addToast('error', `Failed: ${label}`); }
  };

  return (
    <div style={{ overflow: 'auto', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
      
      {/* 1. Velocity (状态映射：保留原版滑块逻辑) */}
      <div className="panel panel-accent-cyan">
        <div className="panel-header"><h3>Order Velocity</h3><span className="badge badge-cyan mono">{velocity.toFixed(1)}x</span></div>
        <div className="panel-body">
          <input type="range" min={0.5} max={3.0} step={0.1} value={velocity} 
            onChange={(e) => { 
              const v = parseFloat(e.target.value); 
              setVelocity(v); 
              debounced(() => fire('Velocity', () => adjustVelocity(v))); 
            }} 
          />
        </div>
      </div>

      {/* 2. Impulse Triggers (弹簧逻辑：用于库存与油价) */}
      <div className="panel panel-accent-orange">
        <div className="panel-header">
          <h3>Crisis Injection</h3>
          <span className="badge badge-orange"><Zap size={9} /> Pulse Mode</span>
        </div>
        <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div style={{ marginBottom: 8 }}>
            <label style={{ display: 'block', fontSize: 10, color: 'var(--text-2)', textTransform: 'uppercase', marginBottom: 3 }}>Target Inventory ID</label>
            <input type="text" value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="Global if empty" style={{ width: '100%' }} />
          </div>

          <SpringSlider 
            label="Inventory Qty Multiplier" 
            accentColor="var(--cyan)"
            onApply={(v) => fire('Qty Pulse', () => triggerCrisis({ 
              inventory_qty_multiplier: v, 
              ...(targetId ? { inventory_target_id: targetId } : {}) 
            }))} 
          />

          <SpringSlider 
            label="Inventory Cost Multiplier" 
            accentColor="var(--orange)"
            onApply={(v) => fire('Cost Pulse', () => triggerCrisis({ 
              inventory_cost_multiplier: v, 
              ...(targetId ? { inventory_target_id: targetId } : {}) 
            }))} 
          />

          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 4 }}>
            <SpringSlider 
              label="Oil Price Multiplier" 
              accentColor="var(--purple)"
              onApply={(v) => fire('Oil Shock', () => triggerCrisis({ 
                oil_price_multiplier: v 
              }))} 
            />
          </div>
        </div>
      </div>

      {/* 3. Inventory Table (保留原版设计) */}
      <div className="panel">
        <div className="panel-header" style={{ cursor: 'pointer' }} onClick={() => setExpandItems(!expandItems)}>
          <h3>{expandItems ? <ChevronDown size={11} /> : <ChevronRight size={11} />} Inventory Detail</h3>
          <span className="text-2" style={{ fontSize: 10 }}>{items.length} items</span>
        </div>
        {expandItems && (
          <div className="panel-body" style={{ padding: 0, maxHeight: 240 }}>
            <table className="data-table">
              <thead><tr><th>Item</th><th className="text-right">Qty</th><th>Action</th></tr></thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="truncate" style={{ maxWidth: 120 }}>{item.name}</td>
                    <td className="text-right mono text-1">{Number(item.qty).toFixed(1)}</td>
                    <td style={{ width: 60 }}>
                      <button className="btn btn-ghost btn-sm" style={{ fontSize: 9 }} onClick={() => setTargetId(item.id)}>Select</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 4. Exchange Rate (保留原版设计) */}
      <div className="panel panel-accent-purple">
        <div className="panel-header"><h3>Exchange Rate (USD/MYR)</h3><span className="badge badge-purple">Live</span></div>
        <div className="panel-body row gap-8">
          <span className="mono text-purple" style={{ fontSize: 16, fontWeight: 700 }}>{exchangeRate?.toFixed(4) ?? '—'}</span>
        </div>
      </div>
    </div>
  );
}