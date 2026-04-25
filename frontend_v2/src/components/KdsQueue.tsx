import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Flame, Clock, AlertTriangle, Pause, ChefHat, MessageSquare } from 'lucide-react';
//import { MOCK_KDS_QUEUE } from '../lib/mockData';

interface KdsOrder {
  id: string;
  order_id?: string;
  table_number?: string | null;
  source?: string | null;
  items: { name: string; quantity: number }[];
  priority: 'urgent' | 'normal' | 'hold';
  status: string;
  position_in_queue: number;
  eta_timestamp?: string | null; 
  agent_note?: string | null;
  created_at: string;
}

const PRIORITY_STYLES: Record<string, { badge: string; icon: any; label: string }> = {
  urgent: { badge: 'badge-red', icon: Flame, label: 'Urgent' },
  normal: { badge: 'badge-green', icon: Clock, label: 'Normal' },
  hold: { badge: 'badge-orange', icon: Pause, label: 'Hold' },
};

export default function KdsQueue() {
  const [queue, setQueue] = useState<KdsOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQueue();

    const channel = supabase
      .channel('kds-realtime')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'kds_queue' },
        () => fetchQueue()
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    const { data } = await supabase
      .from('kds_queue')
      .select('*')
      .neq('status', 'completed')
      .order('position_in_queue', { ascending: true });

    if (data && data.length > 0) {
      setQueue(data.map((d: any) => ({
        ...d,
        items: typeof d.items === 'string' ? JSON.parse(d.items) : (d.items || []),
      })));
    } else {
      setQueue([]);
    }
    setLoading(false);
  };


  const urgentCount = queue.filter((o) => o.priority === 'urgent').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div className="row" style={{ padding: '10px 12px', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div className="row gap-4">
          <ChefHat size={13} color="var(--orange)" />
          <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.3px', color: 'var(--text-1)' }}>
            KDS Queue
          </span>
        </div>
        <div className="row gap-8">
          <span className="text-2" style={{ fontSize: 10 }}>
            Total: <span className="text-0 mono" style={{ fontWeight: 600 }}>{queue.length}</span>
          </span>
          {urgentCount > 0 && (
            <span className="badge badge-red" style={{ fontSize: 9 }}>
              <Flame size={8} /> {urgentCount} Urgent
            </span>
          )}
        </div>
      </div>

      {/* Queue Cards */}
      <div style={{ flex: 1, overflow: 'auto', padding: '8px 10px' }}>
        {loading ? (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <span className="pulse" style={{ color: 'var(--orange)' }}>Loading KDS queue…</span>
          </div>
        ) : queue.length === 0 ? (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <ChefHat size={20} style={{ marginBottom: 6, opacity: 0.4 }} />
            <div>Kitchen queue is empty</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
            {queue.map((order) => {
              const ps = PRIORITY_STYLES[order.priority] || PRIORITY_STYLES.normal;
              const PIcon = ps.icon;
              const etaMinutes = order.eta_timestamp
                ? Math.max(0, Math.floor((new Date(order.eta_timestamp).getTime() - Date.now()) / 60000))
                : null;
              return (
                <div
                  key={order.id}
                  className="slide-in"
                  style={{
                    background: 'var(--glass)',
                    border: `1px solid ${order.priority === 'urgent' ? 'rgba(239,68,68,.3)' : 'var(--glass-border)'}`,
                    borderRadius: 'var(--radius)',
                    padding: '10px 12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    transition: 'border-color var(--ts)',
                  }}
                >
                  {/* Order header */}
                  <div className="row" style={{ justifyContent: 'space-between' }}>
                    <span className="mono" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-0)' }}>
                      #{order.order_id || order.id.slice(-6)}
                    </span>
                    <span className={`badge ${ps.badge}`} style={{ fontSize: 9 }}>
                      <PIcon size={8} /> {ps.label}
                    </span>
                  </div>

                  {/* Table / Source */}
                  {(order.table_number || order.source) && (
                    <div className="text-2" style={{ fontSize: 10 }}>
                      {order.table_number && <span>Table {order.table_number}</span>}
                      {order.table_number && order.source && <span> · </span>}
                      {order.source && <span>{order.source}</span>}
                    </div>
                  )}

                  {/* Items */}
                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: 5 }}>
                    {(order.items || []).map((item, i) => (
                      <div key={i} className="row" style={{ justifyContent: 'space-between', fontSize: 10, padding: '1px 0' }}>
                        <span className="truncate" style={{ maxWidth: 130, color: 'var(--text-1)' }}>{item.name}</span>
                        <span className="mono text-2">×{item.quantity}</span>
                      </div>
                    ))}
                  </div>

                  {/* Footer - ETA */}
                  <div className="row" style={{ justifyContent: 'space-between', marginTop: 'auto', paddingTop: 4, borderTop: '1px solid var(--border-subtle)' }}>
                    {order.eta_timestamp && etaMinutes !== null && (
                      <span className="row gap-4 text-2" style={{ fontSize: 10 }}>
                        <Clock size={9} /> ETA: <span className="mono text-0">{etaMinutes}m</span>
                      </span>
                    )}
                    {order.agent_note && (
                      <span
                        className="row gap-4"
                        style={{ fontSize: 9, color: 'var(--purple)', cursor: 'help' }}
                        title={order.agent_note}
                      >
                        <MessageSquare size={9} /> Note
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
