import { useEffect, useState } from 'react';
import { getPermissions, updatePermissions } from '../lib/api';
import { useToastStore } from '../store/toastStore';

const TOGGLES = [
  { key: 'allow_auto_price_update', label: 'Auto Price Update' },
  { key: 'allow_auto_po_creation', label: 'Auto PO Creation' },
  { key: 'allow_auto_inventory_adjust', label: 'Auto Inventory Adjust' },
  { key: 'allow_auto_marketing_campaign', label: 'Auto Marketing Campaign' },
];
const NUMS = [
  { key: 'max_price_change_percent', label: 'Max Price Change %', def: 15 },
  { key: 'max_spend_amount', label: 'Max Spend Amount ($)', def: 500 },
  { key: 'max_discount_percent', label: 'Max Discount %', def: 30 },
];
const SELECTS = [
  { key: 'approval_mode_for_price_change', label: 'Price Change Mode' },
  { key: 'approval_mode_for_po', label: 'PO Mode' },
  { key: 'approval_mode_for_campaign', label: 'Campaign Mode' },
];

export default function HumanAuthorizationPanel({ onClose }: { onClose: () => void }) {
  const [p, setP] = useState<any>(null);
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    getPermissions().then(setP).catch(() => {
      setP({ allow_auto_price_update: true, allow_auto_po_creation: false, allow_auto_inventory_adjust: true, allow_auto_marketing_campaign: false,
        max_price_change_percent: 15, max_spend_amount: 500, max_discount_percent: 30,
        approval_mode_for_price_change: 'require_approval', approval_mode_for_po: 'require_approval', approval_mode_for_campaign: 'require_approval' });
    });
  }, []);

  const save = async (u: any) => {
    setP(u);
    try { await updatePermissions(u); addToast('success', 'Saved'); } catch { addToast('error', 'Failed'); }
  };

  if (!p) return <div className="auth-overlay" style={{ padding: 20 }}>Loading...</div>;

  return (
    <>
      <div className="auth-backdrop" onClick={onClose} />
      <div className="auth-overlay fade-in">
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, background: 'var(--bg-elevated)', zIndex: 1 }}>
          <div>
            <h3 style={{ fontSize: 13, fontWeight: 600 }}>Agent Permissions</h3>
            <div className="text-2" style={{ fontSize: 10 }}>Define operational boundaries</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Close</button>
        </div>

        <div style={{ padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase' }}>Automation Controls</div>
          {TOGGLES.map((t) => (
            <div key={t.key} className="row" style={{ justifyContent: 'space-between', padding: '4px 0' }}>
              <span style={{ fontSize: 11, color: 'var(--text-1)' }}>{t.label}</span>
              <label className="toggle">
                <input type="checkbox" checked={p[t.key] ?? false} onChange={(e) => save({ ...p, [t.key]: e.target.checked })} />
                <span className="toggle-track" /><span className="toggle-thumb" />
              </label>
            </div>
          ))}

          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 8, marginTop: 4, fontSize: 10, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase' }}>Operational Limits</div>
          {NUMS.map((n) => (
            <div key={n.key} className="row" style={{ justifyContent: 'space-between', padding: '4px 0' }}>
              <span style={{ fontSize: 11, color: 'var(--text-1)' }}>{n.label}</span>
              <input type="number" value={p[n.key] ?? n.def} onChange={(e) => save({ ...p, [n.key]: parseFloat(e.target.value) })} style={{ width: 80, textAlign: 'right', padding: '3px 6px' }} />
            </div>
          ))}

          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 8, marginTop: 4, fontSize: 10, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase' }}>Approval Modes</div>
          {SELECTS.map((s) => (
            <div key={s.key} className="row" style={{ justifyContent: 'space-between', padding: '4px 0' }}>
              <span style={{ fontSize: 11, color: 'var(--text-1)' }}>{s.label}</span>
              <select value={p[s.key] ?? 'require_approval'} onChange={(e) => save({ ...p, [s.key]: e.target.value })} style={{ fontSize: 10 }}>
                <option value="require_approval">Require Approval</option>
                <option value="auto_reject">Auto Reject</option>
              </select>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
