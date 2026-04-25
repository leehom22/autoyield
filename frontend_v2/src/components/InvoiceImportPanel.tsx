import { useState, useRef } from 'react';
import { Upload, FileImage, CheckCircle, AlertCircle, Loader, Clock, X, FileText } from 'lucide-react';
import { uploadInvoice } from '../lib/api';
import { useToastStore } from '../store/toastStore';

interface Rec { id: string; fileName: string; timestamp: string; status: 'extracting' | 'validating' | 'processed' | 'missing_info' | 'debate_triggered' | 'error'; missingFields?: string[]; result?: any; response?: string; debateLogs?: any }

export default function InvoiceImportPanel() {
  const [uploads, setUploads] = useState<Rec[]>(() => { try { const s = localStorage.getItem('ay_inv'); return s ? JSON.parse(s) : []; } catch { return []; } });
  const [sel, setSel] = useState<Rec | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const addToast = useToastStore((s) => s.addToast);
  const addError = useToastStore((s) => s.addError);
  const persist = (l: Rec[]) => { try { localStorage.setItem('ay_inv', JSON.stringify(l.slice(0, 20))); } catch {} };

  const handle = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]; if (!f) return;
    if (f.size > 5 * 1024 * 1024) { addToast('error', 'Max 5 MB'); return; }
    setPreview(URL.createObjectURL(f));
    const rec: Rec = { id: Math.random().toString(36).substr(2, 8), fileName: f.name, timestamp: new Date().toISOString(), status: 'extracting' };
    const list = [rec, ...uploads]; setUploads(list); setSel(rec); setLoading(true);
    try {
      setUploads(list.map((u) => u.id === rec.id ? { ...u, status: 'validating' } : u));
      const r = await uploadInvoice(f);
      let fin: Rec;
      if (r.status === 'incomplete') { fin = { ...rec, status: 'missing_info', missingFields: r.missing_fields }; addToast('warning', `Missing: ${r.missing_fields.join(', ')}`); }
      else if (r.status === 'debate_triggered') { fin = { ...rec, status: 'debate_triggered', response: r.response, debateLogs: r.debate_logs }; addToast('warning', 'Debate triggered'); }
      else { fin = { ...rec, status: 'processed', result: r.result }; addToast('success', 'Processed'); }
      const fl = list.map((u) => u.id === rec.id ? fin : u); setUploads(fl); setSel(fin); persist(fl);
    } catch (err: any) {
      const el = list.map((u) => u.id === rec.id ? { ...u, status: 'error' as const } : u); setUploads(el); setSel({ ...rec, status: 'error' }); addError(err.message); persist(el);
    } finally { setLoading(false); e.target.value = ''; }
  };

  const sIcon = (s: string) => s === 'processed' ? <CheckCircle size={10} color="var(--green)" /> : s === 'error' ? <AlertCircle size={10} color="var(--red)" /> : s === 'missing_info' ? <AlertCircle size={10} color="var(--orange)" /> : s === 'debate_triggered' ? <AlertCircle size={10} color="var(--purple)" /> : <Clock size={10} color="var(--cyan)" />;
  const sBadge = (s: string) => <span className={`badge ${s === 'processed' ? 'badge-green' : s === 'error' ? 'badge-red' : s === 'missing_info' ? 'badge-orange' : s === 'debate_triggered' ? 'badge-purple' : 'badge-cyan'}`}>{s.replace('_', ' ')}</span>;
  const r3 = uploads.slice(0, 3);

  return (
    <div className="flex-col" style={{ height: '100%' }}>
      <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <FileText size={13} color="var(--green)" />
        <span style={{ fontSize: 12, fontWeight: 600 }}>Invoice Import</span>
        <label className="btn btn-ghost btn-sm" style={{ cursor: 'pointer', marginLeft: 'auto' }}>
          <Upload size={11} /> Upload
          <input ref={fileRef} type="file" style={{ display: 'none' }} accept="image/*,.pdf" onChange={handle} disabled={loading} />
        </label>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* Viewer */}
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', background: 'var(--bg-base)', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 90 }}>
          {preview ? (
            <div style={{ position: 'relative', textAlign: 'center', width: '100%' }}>
              <img src={preview} alt="Preview" style={{ maxWidth: '100%', maxHeight: 100, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }} />
              <button onClick={() => setPreview(null)} style={{ position: 'absolute', top: 2, right: 2, background: 'var(--bg-active)', border: 'none', borderRadius: 3, color: 'var(--text-1)', cursor: 'pointer', padding: 2 }}><X size={10} /></button>
            </div>
          ) : (
            <div className="text-2" style={{ textAlign: 'center', fontSize: 10 }}>
              <FileImage size={22} style={{ opacity: .25, marginBottom: 4 }} /><br />Upload invoice or docket (max 5 MB)
            </div>
          )}
        </div>

        {/* Status */}
        {sel && (
          <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)' }}>
            <div className="row gap-4 mb-4">
              <span className="text-2" style={{ fontSize: 10, textTransform: 'uppercase' }}>Status:</span>
              {loading ? <span className="row gap-4 text-cyan" style={{ fontSize: 10 }}><Loader size={10} className="spin" /> Processing...</span> : sBadge(sel.status)}
            </div>
            <div className="mono text-2" style={{ fontSize: 10 }}>{sel.fileName}</div>
          </div>
        )}

        {/* Missing fields */}
        {sel?.missingFields?.length ? (
          <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)', background: 'var(--orange-dim)' }}>
            <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--orange)', textTransform: 'uppercase', marginBottom: 4 }}>Missing Fields</div>
            <div className="row gap-4" style={{ flexWrap: 'wrap' }}>{sel.missingFields.map((f, i) => <span key={i} className="badge badge-orange">{f}</span>)}</div>
            <div className="text-2" style={{ fontSize: 10, marginTop: 4 }}>Re-upload corrected invoice or update inventory.</div>
          </div>
        ) : null}

        {/* Debate */}
        {sel?.status === 'debate_triggered' && sel.response && (
          <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)', background: 'var(--purple-dim)' }}>
            <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--purple)', marginBottom: 4 }}>Debate — Price Spike</div>
            <div style={{ fontSize: 11, color: 'var(--text-1)' }}>{sel.response}</div>
          </div>
        )}

        {/* Result */}
        {sel?.status === 'processed' && sel.result && (
          <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--green)', marginBottom: 4 }}>Extracted</div>
            <pre className="mono text-1" style={{ fontSize: 10, whiteSpace: 'pre-wrap' }}>{JSON.stringify(sel.result, null, 2)}</pre>
          </div>
        )}

        {/* Recent 3 */}
        <div style={{ padding: '8px 14px' }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', marginBottom: 6 }}>Recent ({uploads.length})</div>
          {r3.length === 0 ? <div className="empty-state">No uploads</div> :
            r3.map((u) => (
              <div key={u.id} onClick={() => setSel(u)} style={{
                background: sel?.id === u.id ? 'var(--bg-hover)' : 'var(--bg-base)', border: `1px solid ${sel?.id === u.id ? 'var(--cyan-border)' : 'var(--border)'}`,
                borderRadius: 'var(--radius)', padding: '6px 10px', marginBottom: 4, cursor: 'pointer', transition: 'all var(--ts)',
              }}>
                <div className="row gap-4 mb-2">{sIcon(u.status)}<span className="truncate flex-1" style={{ fontSize: 11 }}>{u.fileName}</span>{sBadge(u.status)}</div>
                <div className="mono text-2" style={{ fontSize: 9 }}>{new Date(u.timestamp).toLocaleString()}</div>
                {u.missingFields && <div className="row gap-4" style={{ flexWrap: 'wrap', marginTop: 3 }}>{u.missingFields.map((f, i) => <span key={i} className="badge badge-orange" style={{ fontSize: 8 }}>{f}</span>)}</div>}
                {u.result && <pre className="mono text-2" style={{ fontSize: 9, marginTop: 3, maxHeight: 32, overflow: 'hidden' }}>{JSON.stringify(u.result, null, 1)}</pre>}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
