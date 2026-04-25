import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useToastStore } from '../store/toastStore';
import { Brain, TrendingUp, Truck, BarChart3, ShieldCheck, FileText } from 'lucide-react';

const F = [
  { icon: Brain, title: 'Dual-Agent Decision Engine', desc: 'Adversarial P-Agent vs R-Agent reasoning on every decision.', c: 'var(--cyan)' },
  { icon: TrendingUp, title: 'Real-time P&L Optimization', desc: 'Dynamic menu pricing driven by live market data.', c: 'var(--green)' },
  { icon: Truck, title: 'Automated Supply Chain', desc: 'Intelligent PO creation and supplier scoring.', c: 'var(--orange)' },
  { icon: BarChart3, title: 'Predictive Forecasting', desc: 'Weekly AI reports with strategic recommendations.', c: 'var(--purple)' },
  { icon: ShieldCheck, title: 'Human-in-the-Loop', desc: 'Configurable approval boundaries for operators.', c: 'var(--cyan)' },
  { icon: FileText, title: 'Invoice OCR Processing', desc: 'AI extraction, validation, and anomaly detection.', c: 'var(--green)' },
];

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const login = useAuthStore((s) => s.login);
  const addToast = useToastStore((s) => s.addToast);
  const navigate = useNavigate();
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (username === 'admin' && password === 'autoyield2026') { login(); navigate('/'); }
    else addToast('error', 'Invalid credentials');
  };

  return (
    <div className="login-container">
      <div className="login-left">
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 500, padding: '0 40px' }}>
          <div className="mb-12">
            <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2, textTransform: 'uppercase', color: 'var(--cyan)', background: 'var(--cyan-dim)', padding: '3px 10px', borderRadius: 3, border: '1px solid var(--cyan-border)' }}>AutoYield v2.0</span>
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 700, lineHeight: 1.25, marginBottom: 10 }}>
            AI-Powered Restaurant<br />
            <span style={{ background: 'linear-gradient(90deg,var(--cyan),var(--purple))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Operations Platform</span>
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-1)', marginBottom: 28, lineHeight: 1.6, maxWidth: 400 }}>
            Real-time simulation engine with dual-agent adversarial reasoning for menu pricing, supply chain optimization, and financial decision-making.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {F.map((f, i) => (
              <div key={i} className="login-feature">
                <div className="lf-icon" style={{ background: `${f.c}11`, border: `1px solid ${f.c}33` }}><f.icon size={15} color={f.c} /></div>
                <div><div style={{ fontWeight: 600, fontSize: 11, marginBottom: 1 }}>{f.title}</div><div style={{ fontSize: 10, color: 'var(--text-2)', lineHeight: 1.3 }}>{f.desc}</div></div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 32, paddingTop: 16, borderTop: '1px solid var(--border)', fontSize: 10, color: 'var(--text-2)' }}>
            Hackathon 2026 · GLM-4 + Supabase Realtime
          </div>
        </div>
      </div>
      <div className="login-right">
        <div style={{ width: '100%', maxWidth: 300 }}>
          <div style={{ marginBottom: 28, textAlign: 'center' }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: 'var(--cyan-dim)', border: '1px solid var(--cyan-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <Brain size={20} color="var(--cyan)" />
            </div>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>Welcome Back</h2>
            <p style={{ fontSize: 11, color: 'var(--text-2)' }}>Sign in to access the operations console</p>
          </div>
          <form onSubmit={handleLogin}>
            <div className="mb-12">
              <label style={{ display: 'block', fontSize: 10, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 5 }}>Username</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="admin" autoFocus />
            </div>
            <div className="mb-12">
              <label style={{ display: 'block', fontSize: 10, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 5 }}>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••••" />
            </div>
            <button type="submit" className="btn btn-primary w-full" style={{ padding: '8px 0', fontSize: 12 }}>Authenticate</button>
          </form>
          <div style={{ textAlign: 'center', marginTop: 16, fontSize: 10, color: 'var(--text-2)' }}>Authorized personnel only</div>
        </div>
      </div>
    </div>
  );
}
