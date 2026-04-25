import { useToastStore } from '../store/toastStore';

export default function ErrorLogPanel() {
  const errors = useToastStore((s) => s.errors);
  return (
    <div className="bottom-terminal-body" style={{ maxHeight: 160 }}>
      {errors.length === 0 ? (
        <div style={{ color: 'var(--text-2)', padding: '4px 0' }}>No errors this session.</div>
      ) : (
        errors.map((e, i) => (
          <div key={i} style={{ padding: '2px 0', borderBottom: '1px solid var(--border-subtle)', display: 'flex', gap: 8 }}>
            <span className="text-2" style={{ flexShrink: 0, fontSize: 10 }}>{new Date(e.timestamp).toLocaleTimeString()}</span>
            <span className="text-red" style={{ fontSize: 11 }}>{e.message}</span>
          </div>
        ))
      )}
    </div>
  );
}
