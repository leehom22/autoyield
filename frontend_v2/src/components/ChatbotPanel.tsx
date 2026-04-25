import { useState, useRef, useEffect } from 'react';
import { Send, Loader, Sparkles, User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChatMessage } from '../lib/api';
import { useToastStore } from '../store/toastStore';

interface Msg {
  role: 'user' | 'agent';
  text: string;
  meta?: { p: string; r: string; rounds: number };
}

export default function ChatbotPanel() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const addToast = useToastStore((s) => s.addToast);
  const addError = useToastStore((s) => s.addError);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [msgs, loading]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMsgs((prev) => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);
    try {
      const response = await sendChatMessage(userMsg);
      setMsgs((prev) => [
        ...prev,
        {
          role: 'agent',
          text: response.response,
          meta: response.p_agent_position
            ? {
                p: response.p_agent_position,
                r: response.r_agent_position,
                rounds: response.debate_rounds,
              }
            : undefined,
        },
      ]);
    } catch (err: any) {
      addError(err.message);
      addToast('error', 'Failed to reach assistant');
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex-col" style={{ height: '100%', background: 'var(--bg-base)' }}>
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          background: 'var(--bg-surface)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 8,
            background: 'linear-gradient(135deg, var(--cyan), var(--blue))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Sparkles size={14} color="white" />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, letterSpacing: '0.3px' }}>
            AutoYield AI Assistant
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-2)' }}>
            P‑Agent · R‑Agent · Executive
          </div>
        </div>
        <div className="status-dot live" style={{ marginRight: 0 }} />
      </div>

      {/* Message List */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {msgs.length === 0 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 12,
              color: 'var(--text-2)',
              textAlign: 'center',
              padding: '0 24px',
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 24,
                background: 'var(--bg-surface)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--border)',
              }}
            >
              <Sparkles size={24} style={{ opacity: 0.4 }} />
            </div>
            <div style={{ fontSize: 12, maxWidth: 260 }}>
              Ask about pricing, procurement, kitchen ops, or strategy.
            </div>
            <div className="row gap-4" style={{ flexWrap: 'wrap', justifyContent: 'center', marginTop: 8 }}>
              {[
                'What’s the impact of rising oil prices?',
                'Analyze last 24h sales performance',
                'Should we run a weekend flash sale?',
              ].map((q, i) => (
                <button
                  key={i}
                  className="btn btn-ghost btn-sm"
                  onClick={() => setInput(q)}
                  style={{ fontSize: 10, padding: '4px 8px' }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {msgs.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
              gap: 6,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
                maxWidth: '85%',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 14,
                  background: msg.role === 'user' ? 'var(--cyan)' : 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div
                className={msg.role === 'user' ? 'chat-user' : 'chat-agent'}
                style={{
                  padding: '10px 14px',
                  borderRadius: 16,
                  background: msg.role === 'user' ? 'var(--cyan)' : 'var(--bg-surface)',
                  color: msg.role === 'user' ? 'white' : 'var(--text-0)',
                  border: msg.role === 'agent' ? '1px solid var(--border)' : 'none',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                  fontSize: 13,
                  lineHeight: 1.5,
                }}
              >
                {msg.role === 'agent' ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p style={{ margin: '0 0 8px 0' }}>{children}</p>,
                      ul: ({ children }) => <ul style={{ margin: '4px 0 8px 16px' }}>{children}</ul>,
                      ol: ({ children }) => <ol style={{ margin: '4px 0 8px 16px' }}>{children}</ol>,
                      li: ({ children }) => <li style={{ marginBottom: 4 }}>{children}</li>,
                      strong: ({ children }) => <strong style={{ color: 'var(--cyan)' }}>{children}</strong>,
                      a: ({ href, children }) => (
                        <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)', textDecoration: 'underline' }}>
                          {children}
                        </a>
                      ),
                    }}
                  >
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                )}
              </div>
            </div>

            {/* Debate meta (P/R agents) */}
            {msg.meta && (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 8,
                  maxWidth: '85%',
                  width: '100%',
                  marginTop: 4,
                  fontSize: 11,
                }}
              >
                <div
                  style={{
                    background: 'var(--bg-active)',
                    padding: '6px 10px',
                    borderRadius: 8,
                    borderLeft: '3px solid var(--cyan)',
                  }}
                >
                  <div style={{ fontWeight: 600, color: 'var(--cyan)', fontSize: 10, marginBottom: 4 }}>
                    P‑Agent · Profit
                  </div>
                  <div style={{ color: 'var(--text-1)', lineHeight: 1.4 }}>{msg.meta.p}</div>
                </div>
                <div
                  style={{
                    background: 'var(--bg-active)',
                    padding: '6px 10px',
                    borderRadius: 8,
                    borderLeft: '3px solid var(--orange)',
                  }}
                >
                  <div style={{ fontWeight: 600, color: 'var(--orange)', fontSize: 10, marginBottom: 4 }}>
                    R‑Agent · Risk
                  </div>
                  <div style={{ color: 'var(--text-1)', lineHeight: 1.4 }}>{msg.meta.r}</div>
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="row" style={{ gap: 8, alignItems: 'center', padding: '4px 0' }}>
            <Loader size={14} className="spin" style={{ color: 'var(--cyan)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-2)' }}>Assistant is thinking...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={send}
        style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-surface)',
          display: 'flex',
          gap: 10,
          alignItems: 'center',
          flexShrink: 0,
        }}
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something… e.g., ‘Optimise menu for this weekend’"
          disabled={loading}
          style={{
            flex: 1,
            background: 'var(--bg-base)',
            border: '1px solid var(--border)',
            borderRadius: 24,
            padding: '8px 16px',
            fontSize: 12,
            outline: 'none',
            transition: 'all 0.2s',
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--cyan)')}
          onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            background: loading || !input.trim() ? 'var(--border)' : 'var(--cyan)',
            border: 'none',
            borderRadius: 24,
            padding: '6px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            color: 'white',
            fontSize: 12,
            fontWeight: 500,
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
          }}
        >
          <Send size={12} />
          Send
        </button>
      </form>
    </div>
  );
}