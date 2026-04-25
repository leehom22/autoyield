import { useState, useEffect, useRef } from 'react';
import { Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useToastStore } from '../../store/toastStore';
import { Activity, Zap, Boxes, MessageSquare, FileText, Shield, ChevronDown, ChevronUp, LogOut, Terminal, Brain, Play, Pause, Wifi, WifiOff } from 'lucide-react';
import ReasoningLogPanel from '../ReasoningLogPanel';
import ApprovalQueuePanel from '../ApprovalQueuePanel';
import ErrorLogPanel from '../ErrorLogPanel';
import HumanAuthorizationPanel from '../HumanAuthorizationPanel';
//import { MOCK_SSE_STATE } from '../../lib/mockData';

export type Tab = 'sandbox' | 'operations' | 'agent-io' | 'report';

export default function DashboardLayout() {
  const logout = useAuthStore((s) => s.logout);
  const errors = useToastStore((s) => s.errors);
  const [activeTab, setActiveTab] = useState<Tab>('sandbox');
  const [termOpen, setTermOpen] = useState(false);
  const [rightOpen, setRightOpen] = useState(true);
  const [authOpen, setAuthOpen] = useState(false);
  const [sseState, setSseState] = useState<any>({ simulated_time: null, is_paused: false, queue_length: 0, velocity: 1 });;
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  // SSE connection
  useEffect(() => {
    const url = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    try {
      const es = new EventSource(`${url}/api/stream/world-state`);
      es.onopen = () => setConnected(true);
      es.onmessage = (e) => { try { setSseState(JSON.parse(e.data)); } catch {} };
      es.onerror = () => setConnected(false);
      esRef.current = es;
    } catch { setConnected(false); }
    return () => { esRef.current?.close(); };
  }, []);

  // Mock simulation time advance
  // useEffect(() => {
  //   if (connected) return;
  //   const iv = setInterval(() => {
  //     setSseState((prev: any) => ({
  //       ...prev,
  //       simulated_time: new Date(new Date(prev.simulated_time || Date.now()).getTime() + 60000).toISOString(),
  //       queue_length: Math.max(0, (prev.queue_length || 5) + Math.floor(Math.random() * 5) - 2),
  //     }));
  //   }, 2000);
  //   return () => clearInterval(iv);
  // }, [connected]);

  const simTime = sseState.simulated_time ? new Date(sseState.simulated_time) : null;
  const tabs: { key: Tab; icon: any; label: string }[] = [
    { key: 'sandbox', icon: Zap, label: 'Sandbox' },
    { key: 'operations', icon: Boxes, label: 'Operations' },
    { key: 'agent-io', icon: MessageSquare, label: 'Agent I/O' },
    { key: 'report', icon: FileText, label: 'Reports' },
  ];

  return (
    <div className="flex-col" style={{ height: '100vh' }}>
      {/* ── Status Bar ────────────────── */}
      <div className="status-bar">
        <div className="sb-section"><span className="status-dot live" /><span style={{ fontWeight: 600, color: 'var(--cyan)' }}>SIM</span></div>
        <div className="sb-section mono text-1">
          {simTime ? simTime.toLocaleDateString('en-MY', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' }) : '—'}
          <span className="text-cyan" style={{ fontWeight: 600 }}>{simTime ? simTime.toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}</span>
        </div>
        <div className="sb-divider" />
        <div className="sb-section">
          {sseState.is_paused
            ? <><span className="badge badge-orange" style={{ fontSize: 9 }}><Pause size={9} /> Paused</span><span className="text-2" style={{ fontSize: 10 }}>Agent is thinking...</span></>
            : <span className="badge badge-green" style={{ fontSize: 9 }}><Play size={9} /> Running</span>}
        </div>
        <div className="sb-section mono text-2">Queue: <span className="text-0">{sseState.queue_length ?? 0}</span></div>
        <div style={{ marginLeft: 'auto' }} className="sb-section">
          {connected ? <><Wifi size={11} color="var(--green)" /><span className="text-green" style={{ fontSize: 10 }}>Connected</span></> : <><WifiOff size={11} color="var(--text-2)" /><span className="text-2" style={{ fontSize: 10 }}>Mock</span></>}
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* ── Left Sidebar ──────────── */}
        <aside style={{ width: 200, background: 'var(--bg-surface)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 22, height: 22, borderRadius: 4, background: 'var(--cyan-dim)', border: '1px solid var(--cyan-border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Terminal size={12} color="var(--cyan)" />
            </div>
            <div><div style={{ fontSize: 12, fontWeight: 700 }}>AutoYield</div><div style={{ fontSize: 8, color: 'var(--text-2)', letterSpacing: '0.5px' }}>OPS CONSOLE</div></div>
          </div>
          <nav style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
            {tabs.map((t) => <NavBtn key={t.key} icon={t.icon} label={t.label} active={activeTab === t.key} onClick={() => setActiveTab(t.key)} />)}
            <div style={{ padding: '10px 12px 3px' }}><span style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '.5px' }}>Controls</span></div>
            <NavBtn icon={Shield} label="Permissions" active={authOpen} onClick={() => setAuthOpen(!authOpen)} />
            <NavBtn icon={Brain} label={rightOpen ? 'Hide Agent' : 'Show Agent'} active={false} onClick={() => setRightOpen(!rightOpen)} />
          </nav>
          <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border)' }}>
            <button className="btn btn-ghost w-full" style={{ justifyContent: 'flex-start', fontSize: 11 }} onClick={logout}><LogOut size={12} /> Sign Out</button>
          </div>
        </aside>

        {/* ── Center ──────────────── */}
        <div className="flex-col" style={{ flex: 1, minWidth: 0 }}>
          <Outlet context={{ activeTab, sseState }} />
        </div>

        {/* ── Right Panel ──────────── */}
        {rightOpen && (
          <div className="right-panel">
            <div className="right-panel-header">
              <div className="rp-title"><span className="status-dot live" /> AI Agent</div>
              <span className="badge badge-cyan" style={{ fontSize: 9 }}>Realtime</span>
            </div>
            <ReasoningLogPanel />
            <ApprovalQueuePanel />
          </div>
        )}
      </div>

      {/* ── Bottom Terminal ───────── */}
      <div className="bottom-terminal" style={{ height: termOpen ? 180 : 26 }}>
        <div className="bottom-terminal-header" onClick={() => setTermOpen(!termOpen)}>
          <div className="row gap-4" style={{ flex: 1 }}>
            <span className="bt-tab"><Activity size={9} /> Errors</span>
            {errors.length > 0 && <span style={{ fontSize: 9, background: 'var(--red)', color: '#fff', padding: '0 4px', borderRadius: 2 }}>{errors.length}</span>}
          </div>
          {termOpen ? <ChevronDown size={11} color="var(--text-2)" /> : <ChevronUp size={11} color="var(--text-2)" />}
        </div>
        {termOpen && <ErrorLogPanel />}
      </div>

      {authOpen && <HumanAuthorizationPanel onClose={() => setAuthOpen(false)} />}
    </div>
  );
}

function NavBtn({ icon: Icon, label, active, onClick }: { icon: any; label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 7, width: '100%', padding: '7px 12px',
      background: active ? 'var(--bg-hover)' : 'transparent', border: 'none',
      color: active ? 'var(--text-0)' : 'var(--text-1)', cursor: 'pointer', fontSize: 12, textAlign: 'left',
      borderRight: active ? '2px solid var(--cyan)' : '2px solid transparent', transition: 'all var(--ts)',
    }}
      onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--bg-hover)'; }}
      onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = active ? 'var(--bg-hover)' : 'transparent'; }}
    ><Icon size={14} />{label}</button>
  );
}
