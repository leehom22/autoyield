import { useToastStore } from '../store/toastStore';
import { X } from 'lucide-react';

export default function NotificationToast() {
  const { toasts, removeToast } = useToastStore();
  const bc = (t: string) => t === 'success' ? 'var(--green)' : t === 'error' ? 'var(--red)' : t === 'warning' ? 'var(--orange)' : 'var(--cyan)';

  return (
    <div style={{ position: 'fixed', top: 8, right: 8, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 4, maxWidth: 320 }}>
      {toasts.map((t) => (
        <div key={t.id} className="fade-in" style={{
          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
          borderLeft: `3px solid ${bc(t.type)}`, borderRadius: 'var(--radius)',
          padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 8, fontSize: 11,
        }}>
          <span style={{ flex: 1 }}>{t.message}</span>
          <button onClick={() => removeToast(t.id)} style={{ background: 'none', border: 'none', color: 'var(--text-2)', cursor: 'pointer', padding: 0, display: 'flex' }}><X size={12} /></button>
        </div>
      ))}
    </div>
  );
}
