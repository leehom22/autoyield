import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { MOCK_DECISIONS } from '../lib/mockData';
import { ChevronDown, ChevronRight, Brain } from 'lucide-react';

export default function ReasoningLogPanel() {
  const [logs, setLogs] = useState<any[]>(MOCK_DECISIONS);
  const [collapsed, setCollapsed] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    supabase.from('decision_logs').select('*').order('timestamp', { ascending: false }).limit(25).then(({ data }) => { if (data?.length) setLogs(data); });
    const sub = supabase.channel('lr3').on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'decision_logs' }, (p) => {
      setLogs((prev) => [p.new, ...prev].slice(0, 40));
    }).subscribe();
    return () => { supabase.removeChannel(sub); };
  }, []);

  return (
    <div className="right-section" style={{ flex: collapsed ? '0 0 auto' : 1, minHeight: 0 }}>
      <div className="right-section-header" onClick={() => setCollapsed(!collapsed)}>
        <div className="row gap-4">
          {collapsed ? <ChevronRight size={11} /> : <ChevronDown size={11} />}
          <Brain size={11} color="var(--cyan)" /><span>Reasoning Log</span>
        </div>
        <span style={{ fontSize: 9, background: 'var(--bg-active)', padding: '0 5px', borderRadius: 2 }}>{logs.length}</span>
      </div>
      {!collapsed && (
        <div className="right-section-body">
          {logs.map((l) => {
            const ex = expandedId === l.id;
            return (
              <div key={l.id} style={{ borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer' }} onClick={() => setExpandedId(ex ? null : l.id)}>
                <div style={{ padding: '6px 12px' }}>
                  <div className="row gap-4 mb-4" style={{ flexWrap: 'wrap' }}>
                    <span className={`badge ${l.trigger_signal === 'WEEKLY_FORECAST' ? 'badge-cyan' : l.trigger_signal === 'LOW_INVENTORY' ? 'badge-red' : 'badge-orange'}`} style={{ fontSize: 9 }}>{l.trigger_signal}</span>
                    {l.resolution && <span className="badge badge-purple" style={{ fontSize: 9 }}>{l.resolution}</span>}
                    <span className="mono text-2" style={{ fontSize: 9, marginLeft: 'auto' }}>{new Date(l.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="truncate text-1" style={{ fontSize: 11 }}>{l.action_taken?.substring(0, 80) || '—'}</div>
                </div>
                {ex && (
                  <div style={{ padding: '4px 12px 10px', background: 'var(--bg-base)' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, marginBottom: 6 }}>
                      <div style={{ padding: '5px 8px', borderLeft: '2px solid var(--cyan)', background: 'var(--bg-surface)', borderRadius: 3 }}>
                        <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--cyan)', marginBottom: 3 }}>P-AGENT</div>
                        <div style={{ fontSize: 10, color: 'var(--text-1)', whiteSpace: 'pre-wrap', lineHeight: 1.4 }}>{l.p_agent_argument || '—'}</div>
                      </div>
                      <div style={{ padding: '5px 8px', borderLeft: '2px solid var(--orange)', background: 'var(--bg-surface)', borderRadius: 3 }}>
                        <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--orange)', marginBottom: 3 }}>R-AGENT</div>
                        <div style={{ fontSize: 10, color: 'var(--text-1)', whiteSpace: 'pre-wrap', lineHeight: 1.4 }}>{l.r_agent_argument || '—'}</div>
                      </div>
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-0)', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{l.action_taken}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
