import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { BookOpen, ChevronDown, ChevronRight, Sparkles } from 'lucide-react';
//import { MOCK_KNOWLEDGE_BASE } from '../lib/mockData';

interface KnowledgeRecord {
  id: string;
  scenario_description: string;
  lesson_learned: string;
  performance_score: number;
  created_at: string;
}

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return `${Math.floor(days / 7)}w ago`;
}

export default function KnowledgeBase() {
  const [records, setRecords] = useState<KnowledgeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchData();

    const channel = supabase
      .channel('knowledge-realtime')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'knowledge_base' },
        (payload) => {
          setRecords((prev) => [payload.new as KnowledgeRecord, ...prev].slice(0, 10));
        }
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  const fetchData = async () => {
    setLoading(true);
    const { data } = await supabase.from('knowledge_base').select('*').order('created_at', { ascending: false }).limit(10);
    setRecords(data || []);
    setLoading(false);
  };

  const toggle = (id: string) => setExpandedId(expandedId === id ? null : id);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="row" style={{ padding: '10px 12px', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div className="row gap-4">
          <BookOpen size={13} color="var(--purple)" />
          <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.3px', color: 'var(--text-1)' }}>
            Knowledge Base
          </span>
          <span className="badge badge-purple" style={{ fontSize: 9 }}>
            <Sparkles size={8} /> RAG Learning
          </span>
        </div>
        <span className="text-2" style={{ fontSize: 10 }}>{records.length} lessons</span>
      </div>

      <div style={{ overflow: 'auto', padding: '6px 10px' }}>
        {loading ? (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <span className="pulse" style={{ color: 'var(--purple)' }}>Loading knowledge base…</span>
          </div>
        ) : records.length === 0 ? (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <BookOpen size={20} style={{ marginBottom: 6, opacity: 0.4 }} />
            <div>No knowledge records yet</div>
          </div>
        ) : (
          records.map((rec) => {
            const expanded = expandedId === rec.id;
            const scorePct = Math.round((rec.performance_score ?? 0) * 100);
            const scoreColor = scorePct >= 80 ? 'var(--green)' : scorePct >= 50 ? 'var(--orange)' : 'var(--red)';

            return (
              <div
                key={rec.id}
                onClick={() => toggle(rec.id)}
                className="fade-in"
                style={{
                  background: expanded ? 'var(--bg-hover)' : 'transparent',
                  border: '1px solid',
                  borderColor: expanded ? 'var(--border)' : 'var(--border-subtle)',
                  borderRadius: 'var(--radius)',
                  padding: '8px 10px',
                  marginBottom: 4,
                  cursor: 'pointer',
                  transition: 'all var(--ts)',
                }}
              >
                {/* Header row */}
                <div className="row" style={{ justifyContent: 'space-between', gap: 8 }}>
                  <div className="row gap-4" style={{ flex: 1, minWidth: 0 }}>
                    {expanded ? <ChevronDown size={11} color="var(--text-2)" /> : <ChevronRight size={11} color="var(--text-2)" />}
                    <span className={expanded ? '' : 'truncate'} style={{ fontSize: 11, color: 'var(--text-0)', flex: 1 }}>
                      {rec.scenario_description}
                    </span>
                  </div>
                  <div className="row gap-8" style={{ flexShrink: 0 }}>
                    {/* Score bar */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <div style={{
                        width: 40,
                        height: 4,
                        background: 'var(--bg-active)',
                        borderRadius: 2,
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          width: `${scorePct}%`,
                          height: '100%',
                          background: scoreColor,
                          borderRadius: 2,
                          transition: 'width 0.3s ease',
                        }} />
                      </div>
                      <span className="mono" style={{ fontSize: 9, color: scoreColor, fontWeight: 600 }}>{scorePct}%</span>
                    </div>
                    <span className="text-2" style={{ fontSize: 9, whiteSpace: 'nowrap' }}>{relativeTime(rec.created_at)}</span>
                  </div>
                </div>

                {/* Expanded content */}
                {expanded && (
                  <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: 10, color: 'var(--text-2)', marginBottom: 3, textTransform: 'uppercase', letterSpacing: '.3px' }}>
                      Lesson Learned
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-1)', lineHeight: 1.5 }}>
                      {rec.lesson_learned}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
