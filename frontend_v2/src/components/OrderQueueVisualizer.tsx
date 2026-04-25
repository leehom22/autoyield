import { useEffect, useState, useRef } from 'react';
import { supabase } from '../lib/supabase';
//import { generateMockOrder } from '../lib/mockData';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface Order { id: string; items: any; total_revenue: number; total_margin: number; timestamp: string; customer_segment: string; }

export default function OrderQueueVisualizer({ sseState }: { sseState: any }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hasSub, setHasSub] = useState(false);

  // useEffect(() => {
  //   const sub = supabase.channel('orders_rt3').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'orders' }, (p) => {
  //     setHasSub(true);
  //     setOrders((prev) => [p.new as Order, ...prev].slice(0, 30));
  //   }).subscribe();
  //   return () => { supabase.removeChannel(sub); };
  // }, []);

  useEffect(() => {
  // Initial loads recent 30 orders
  supabase.from('orders').select('*').order('timestamp', { ascending: false }).limit(30)
    .then(({ data }) => { if (data) setOrders(data); });

  const sub = supabase.channel('orders_rt3')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'orders' }, (p) => {
      setHasSub(true);
      setOrders((prev) => [p.new as Order, ...prev].slice(0, 30));
    })
    .subscribe();
  return () => { supabase.removeChannel(sub); };
}, []);

  // Mock order generator when no real data
  // useEffect(() => {
  //   if (hasSub) return;
  //   // Seed some initial orders
  //   setOrders(Array.from({ length: 8 }, () => generateMockOrder()).reverse());
  //   const iv = setInterval(() => {
  //     setOrders((prev) => [generateMockOrder(), ...prev].slice(0, 30));
  //   }, 3000);
  //   return () => clearInterval(iv);
  // }, [hasSub]);

  useEffect(() => { if (containerRef.current) containerRef.current.scrollTop = 0; }, [orders.length]);

  const parseItems = (items: any): string => {
    if (!items) return '—';
    if (typeof items === 'string') { try { const a = JSON.parse(items); return Array.isArray(a) ? a.map((i: any) => i.name || i).join(', ') : items; } catch { return items; } }
    if (Array.isArray(items)) return items.map((i: any) => i.name || String(i)).join(', ');
    return String(items);
  };

  return (
    <div className="flex-col" style={{ height: '100%' }}>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8, background: 'var(--bg-surface)', flexShrink: 0 }}>
        <span className="status-dot live" />
        <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.5px', color: 'var(--text-1)' }}>Live Orders</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          {sseState?.is_paused && <span className="badge badge-orange pulse" style={{ fontSize: 9 }}>Agent Thinking</span>}
          <span className="badge badge-cyan mono" style={{ fontSize: 9 }}>Q: {sseState?.queue_length ?? 0}</span>
          <span className="mono text-2" style={{ fontSize: 10 }}>{orders.length} recv</span>
        </div>
      </div>
      <div ref={containerRef} style={{ flex: 1, overflow: 'auto' }}>
        <table className="data-table">
          <thead><tr>
            <th style={{ width: 75 }}>Time</th><th>Items</th><th>Segment</th>
            <th className="text-right" style={{ width: 70 }}>Revenue</th><th className="text-right" style={{ width: 70 }}>Margin</th>
          </tr></thead>
          <tbody>
            {orders.map((o, i) => (
              <tr key={o.id} className={i === 0 ? 'slide-in' : ''}>
                <td className="mono text-2" style={{ fontSize: 10 }}>{new Date(o.timestamp).toLocaleTimeString()}</td>
                <td className="truncate" style={{ maxWidth: 180, fontSize: 11 }}>{parseItems(o.items)}</td>
                <td><span className="badge badge-cyan" style={{ fontSize: 9 }}>{o.customer_segment}</span></td>
                <td className="text-right mono">${(o.total_revenue ?? 0).toFixed(2)}</td>
                <td className="text-right">
                  <span style={{ color: (o.total_margin ?? 0) >= 0 ? 'var(--green)' : 'var(--red)', display: 'inline-flex', alignItems: 'center', gap: 2 }} className="mono">
                    {(o.total_margin ?? 0) >= 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}${Math.abs(o.total_margin ?? 0).toFixed(2)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
