import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { approveNotification } from '../lib/api';
import { useToastStore } from '../store/toastStore';
//import { MOCK_NOTIFICATIONS } from '../lib/mockData';
import { Check, X, ChevronDown, ChevronRight, Bell, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

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
              <div key={n.id} className="slide-in" style={{ borderBottom: '1px solid var(--border-subtle)', padding: '12px 14px' }}>
                
                {/* 1. Header */}
                <div className="row gap-4 mb-4">
                  <span className={`badge ${n.priority === 'high' ? 'badge-red' : 'badge-orange'}`} style={{ fontSize: 9 }}>
                    {n.priority.toUpperCase()}
                  </span>
                  <span className="mono text-2" style={{ fontSize: 9, marginLeft: 'auto' }}>
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                </div>

                {/* 2. Message*/}
                <div style={{ 
                  fontSize: '11.5px',
                  marginBottom: 12, 
                  lineHeight: 1.6, 
                  color: 'var(--text-1)' 
                }} className="markdown-body">
                  <ReactMarkdown components={{
                    p: ({children}) => <p style={{ marginBottom: 8 }}>{children}</p>,
                    strong: ({children}) => <strong style={{ color: 'var(--text-0)', fontWeight: 700 }}>{children}</strong>,
                    li: ({children}) => <li style={{ marginBottom: 4, marginLeft: 12 }}>{children}</li>,
                    code: ({children}) => <code style={{ background: 'var(--bg-active)', padding: '2px 4px', borderRadius: 3, fontFamily: 'var(--mono)' }}>{children}</code>
                  }}>
                    {n.message}
                  </ReactMarkdown>
                </div>

                {/* 3. Proposed Action*/}
                {n.proposed_action && (
                  <div style={{ 
                    background: 'linear-gradient(145deg, var(--bg-surface), var(--bg-base))', 
                    border: '1px solid var(--border-subtle)', 
                    borderRadius: 8, 
                    padding: '10px', 
                    marginBottom: 14,
                    boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.05)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, fontWeight: 600, color: 'var(--cyan)', marginBottom: 8 }}>
                      <Zap size={10} /> AGENT PROPOSAL DATA
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      {Object.entries(n.proposed_action).map(([key, value]) => {
                        if (typeof value === 'object') return null;
                        return (
                          <div key={key} style={{ display: 'flex', flexDirection: 'column', borderLeft: '2px solid var(--border)', paddingLeft: 8 }}>
                            <span style={{ fontSize: 9, color: 'var(--text-2)', textTransform: 'uppercase' }}>{key.replace(/_/g, ' ')}</span>
                            <span className="mono" style={{ fontSize: 11, color: 'var(--text-0)', fontWeight: 500 }}>
                              {key.toLowerCase().includes('price') ? `RM${value}` : String(value)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 4. Action Buttons */}
                {noteFor === n.id ? (
                  <div className="row gap-4 slide-in">
                    <input 
                      type="text" 
                      value={note} 
                      onChange={(e) => setNote(e.target.value)} 
                      placeholder="Add operator note..." 
                      style={{ flex: 1, padding: '4px 8px', fontSize: 10, background: 'var(--bg-base)', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--text-0)' }} 
                    />
                    <button className="btn btn-primary btn-sm" disabled={busy === n.id} onClick={() => act(n.id, true)}>Confirm</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setNoteFor(null)}>Cancel</button>
                  </div>
                ) : (
                  <div className="row gap-4">
                    <button className="btn btn-success btn-sm" disabled={busy === n.id} onClick={() => setNoteFor(n.id)} style={{ flex: 1, justifyContent: 'center' }}>
                      <Check size={12} style={{ marginRight: 4 }} /> Approve
                    </button>
                    <button className="btn btn-danger btn-sm" disabled={busy === n.id} onClick={() => act(n.id, false)} style={{ flex: 1, justifyContent: 'center' }}>
                      <X size={12} style={{ marginRight: 4 }} /> Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
