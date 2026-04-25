import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { approveNotification } from '../lib/api';
import { useToastStore } from '../store/toastStore';
//import { MOCK_NOTIFICATIONS } from '../lib/mockData';
import { Check, X, ChevronDown, ChevronRight, Bell } from 'lucide-react';

export default function ApprovalQueuePanel() {
  const [notifs, setNotifs] = useState<any[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [noteFor, setNoteFor] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    supabase.from('notifications').select('*').eq('status', 'pending').order('created_at', { ascending: false }).then(({ data }) => { if (data?.length) setNotifs(data); });
    const sub = supabase.channel('nr2').on('postgres_changes', { event: '*', schema: 'public', table: 'notifications' }, (p) => {
      if (p.eventType === 'INSERT' && (p.new as any).status === 'pending') setNotifs((prev) => [p.new, ...prev]);
      else if (p.eventType === 'UPDATE' && (p.new as any).status !== 'pending') setNotifs((prev) => prev.filter((n) => n.id !== (p.new as any).id));
    }).subscribe();
    return () => { supabase.removeChannel(sub); };
  }, []);

  const act = async (id: string, approved: boolean) => {
    setBusy(id);
    try { await approveNotification(id, approved, note); addToast('success', approved ? 'Approved' : 'Rejected'); setNotifs((p) => p.filter((n) => n.id !== id)); setNoteFor(null); setNote(''); }
    catch { addToast('error', 'Failed'); } finally { setBusy(null); }
  };

  return (
    <div className="right-section" style={{ flex: collapsed ? '0 0 auto' : 1, minHeight: 0 }}>
      <div className="right-section-header" onClick={() => setCollapsed(!collapsed)}>
        <div className="row gap-4">
          {collapsed ? <ChevronRight size={11} /> : <ChevronDown size={11} />}
          <Bell size={11} color="var(--orange)" /><span>Approvals</span>
        </div>
        {notifs.length > 0 && <span style={{ fontSize: 9, background: 'var(--red)', color: '#fff', padding: '0 5px', borderRadius: 2, fontWeight: 600 }}>{notifs.length}</span>}
      </div>
      {!collapsed && (
        <div className="right-section-body">
          {notifs.length === 0 ? <div className="empty-state">No pending</div> :
            notifs.map((n) => (
              <div key={n.id} style={{ borderBottom: '1px solid var(--border-subtle)', padding: '8px 12px' }}>
                <div className="row gap-4 mb-4">
                  <span className={`badge ${n.priority === 'high' ? 'badge-red' : 'badge-orange'}`} style={{ fontSize: 9 }}>{n.priority}</span>
                  <span className="mono text-2" style={{ fontSize: 9, marginLeft: 'auto' }}>{new Date(n.created_at).toLocaleString()}</span>
                </div>
                <div style={{ fontSize: 11, marginBottom: 4 }}>{n.message}</div>
                {n.proposed_action && <pre className="mono text-2" style={{ fontSize: 9, maxHeight: 40, overflow: 'hidden', whiteSpace: 'pre-wrap', marginBottom: 4 }}>{JSON.stringify(n.proposed_action, null, 1)}</pre>}
                {noteFor === n.id ? (
                  <div className="row gap-4">
                    <input type="text" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note..." style={{ flex: 1, padding: '3px 6px', fontSize: 10 }} />
                    <button className="btn btn-primary btn-sm" disabled={busy === n.id} onClick={() => act(n.id, true)}>OK</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setNoteFor(null)}>×</button>
                  </div>
                ) : (
                  <div className="row gap-4">
                    <button className="btn btn-success btn-sm" disabled={busy === n.id} onClick={() => setNoteFor(n.id)}><Check size={10} /> Approve</button>
                    <button className="btn btn-danger btn-sm" disabled={busy === n.id} onClick={() => act(n.id, false)}><X size={10} /></button>
                  </div>
                )}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
