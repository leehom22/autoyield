import { useState, useRef, useEffect } from 'react';
import { Send, Loader, Sparkles } from 'lucide-react';
import { sendChatMessage } from '../lib/api';
import { useToastStore } from '../store/toastStore';

interface Msg { role: 'user' | 'agent'; text: string; meta?: { p: string; r: string; rounds: number } }

export default function ChatbotPanel() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const addToast = useToastStore((s) => s.addToast);
  const addError = useToastStore((s) => s.addError);

  useEffect(() => { ref.current?.scrollTo(0, ref.current.scrollHeight); }, [msgs, loading]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const m = input; setInput('');
    setMsgs((p) => [...p, { role: 'user', text: m }]);
    setLoading(true);
    try {
      const r = await sendChatMessage(m);
      setMsgs((p) => [...p, { role: 'agent', text: r.response, meta: r.p_agent_position ? { p: r.p_agent_position, r: r.r_agent_position, rounds: r.debate_rounds } : undefined }]);
    } catch (err: any) { addError(err.message); addToast('error', 'Chat failed'); }
    finally { setLoading(false); }
  };

  return (
    <div className="flex-col" style={{ height: '100%' }}>
      <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <Sparkles size={13} color="var(--cyan)" />
        <span style={{ fontSize: 12, fontWeight: 600 }}>Agent Chat</span>
        <span className="text-2" style={{ fontSize: 10, marginLeft: 'auto' }}>POST /api/chat</span>
      </div>

      <div ref={ref} style={{ flex: 1, overflowY: 'auto', padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {msgs.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: 8, color: 'var(--text-2)' }}>
            <Sparkles size={24} style={{ opacity: 0.3 }} />
            <span style={{ fontSize: 11 }}>Ask the AI agent a question about your restaurant operations</span>
            <div className="row gap-4" style={{ flexWrap: 'wrap', justifyContent: 'center', marginTop: 8 }}>
              {['What should I do about rising oil prices?', 'Analyze today\'s sales performance', 'Should I run a weekend promo?'].map((q, i) => (
                <button key={i} className="btn btn-ghost btn-sm" onClick={() => { setInput(q); }} style={{ fontSize: 10 }}>{q}</button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: m.role === 'user' ? 'flex-end' : 'flex-start', gap: 3 }}>
            <div className={m.role === 'user' ? 'chat-user' : 'chat-agent'} style={{ maxWidth: '85%' }}>{m.text}</div>
            {m.meta && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, maxWidth: '85%', width: '100%' }}>
                <div style={{ background: 'var(--bg-base)', padding: '4px 8px', borderRadius: 3, borderLeft: '2px solid var(--cyan)', fontSize: 10 }}>
                  <span className="text-cyan" style={{ fontSize: 9, fontWeight: 600 }}>P: </span><span className="text-1">{m.meta.p}</span>
                </div>
                <div style={{ background: 'var(--bg-base)', padding: '4px 8px', borderRadius: 3, borderLeft: '2px solid var(--orange)', fontSize: 10 }}>
                  <span className="text-orange" style={{ fontSize: 9, fontWeight: 600 }}>R: </span><span className="text-1">{m.meta.r}</span>
                </div>
              </div>
            )}
          </div>
        ))}
        {loading && <div className="row text-2" style={{ fontSize: 11, gap: 6 }}><Loader size={12} className="spin" /> Thinking...</div>}
      </div>

      <form onSubmit={send} className="row gap-4" style={{ padding: '8px 14px', borderTop: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
        <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask the agent..." disabled={loading} style={{ flex: 1 }} />
        <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()} style={{ padding: '6px 12px' }}><Send size={12} /></button>
      </form>
    </div>
  );
}
