import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { X, MessageCircle, Phone, Mail } from 'lucide-react';
//import { MOCK_SUPPLIER_CONTACT_LOGS } from '../lib/mockData';

interface ContactLog {
  id: string;
  supplier_id: string;
  created_at: string;
  message_type: string;
  message_body: string; 
  quantity?: number | null;
  unit_price?: number | null;
  channel: string;
  status: string;
}

const MSG_TYPE_STYLES: Record<string, string> = {
  inquiry: 'badge-cyan',
  quote: 'badge-purple',
  order: 'badge-green',
  complaint: 'badge-red',
  follow_up: 'badge-orange',
  negotiation: 'badge-orange',
};

const STATUS_STYLES: Record<string, string> = {
  sent: 'badge-cyan',
  received: 'badge-green',
  pending: 'badge-orange',
  failed: 'badge-red',
  read: 'badge-purple',
};

const CHANNEL_ICONS: Record<string, any> = {
  whatsapp: MessageCircle,
  phone: Phone,
  email: Mail,
  sms: MessageCircle,
};

interface Props {
  supplierId: string;
  supplierName: string;
  onClose: () => void;
}

export default function SupplierContactLogsModal({ supplierId, supplierName, onClose }: Props) {
  const [logs, setLogs] = useState<ContactLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();

    const channel = supabase
      .channel(`supplier-contacts-${supplierId}`)
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'supplier_contact_logs', filter: `supplier_id=eq.${supplierId}` },
        (payload) => {
          setLogs((prev) => [payload.new as ContactLog, ...prev].slice(0, 20));
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [supplierId]);

  const fetchLogs = async () => {
    setLoading(true);
    const { data } = await supabase
      .from('supplier_contact_logs')
      .select('*')
      .eq('supplier_id', supplierId)
      .order('created_at', { ascending: false })
      .limit(20);

    setLogs(data || []);
    setLoading(false);
  };

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,.55)',
          backdropFilter: 'blur(4px)',
          zIndex: 300,
        }}
      />

      {/* Modal */}
      <div
        className="fade-in"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 'min(720px, 90vw)',
          maxHeight: '80vh',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 301,
          boxShadow: '0 16px 48px rgba(0,0,0,.5)',
        }}
      >
        {/* Modal Header */}
        <div className="row" style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border)',
          justifyContent: 'space-between',
          flexShrink: 0,
          background: 'linear-gradient(135deg, rgba(34,211,238,.03), rgba(167,139,250,.03))',
        }}>
          <div className="row gap-8">
            <MessageCircle size={14} color="var(--cyan)" />
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-0)' }}>Contact Logs</div>
              <div style={{ fontSize: 10, color: 'var(--text-2)' }}>{supplierName}</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost btn-sm"
            style={{ padding: 4, minWidth: 0 }}
          >
            <X size={14} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          {loading ? (
            <div className="empty-state" style={{ padding: '40px 0' }}>
              <span className="pulse" style={{ color: 'var(--cyan)' }}>Loading contact logs…</span>
            </div>
          ) : logs.length === 0 ? (
            <div className="empty-state" style={{ padding: '40px 0' }}>
              <MessageCircle size={20} style={{ marginBottom: 6, opacity: 0.4 }} />
              <div>No contact logs for this supplier</div>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Type</th>
                  <th>Message</th>
                  <th className="text-right">Qty</th>
                  <th className="text-right">Unit Price</th>
                  <th>Channel</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const ChIcon = CHANNEL_ICONS[log.channel] || MessageCircle;
                  return (
                    <tr key={log.id}>
                      <td className="mono text-2" style={{ fontSize: 10, whiteSpace: 'nowrap' }}>
                        {new Date(log.created_at).toLocaleString('en-MY', {
                          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                        })}
                      </td>
                      <td>
                        <span className={`badge ${MSG_TYPE_STYLES[log.message_type] || 'badge-cyan'}`}>
                          {log.message_type?.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="truncate" style={{ maxWidth: 180, fontSize: 11 }}>
                        {log.message_body?.substring(0, 80)}...
                      </td>
                      <td className="text-right mono">{log.quantity ?? '—'}</td>
                      <td className="text-right mono">{log.unit_price != null ? `$${log.unit_price.toFixed(2)}` : '—'}</td>
                      <td>
                        <span className="row gap-4 text-2" style={{ fontSize: 10 }}>
                          <ChIcon size={10} /> {log.channel}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${STATUS_STYLES[log.status] || 'badge-cyan'}`}>
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
