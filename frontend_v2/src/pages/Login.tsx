import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useToastStore } from '../store/toastStore';
import { Brain, TrendingUp, Truck, BarChart3, ShieldCheck, FileText } from 'lucide-react';

const F = [
  { 
    icon: Brain, title: 'Dual-Agent Debate', badge: '< 10s', c: 'var(--cyan)',
    desc: 'P-Agent (Profit) vs R-Agent (Risk) – triggered by price spikes, stockouts, or surges.' 
  },
  { 
    icon: TrendingUp, title: 'Real-time Margin Protection', badge: '8D Sense', c: 'var(--green)',
    desc: '8-dimensional sensing (inventory, supplier, staff, macro, festivals, orders) → auto-price.' 
  },
  { 
    icon: Truck, title: 'Autonomous Procurement', badge: 'Spike→PO', c: 'var(--orange)',
    desc: 'Auto-detect spikes → evaluate alternatives → contact supplier → create PO.' 
  },
  { 
    icon: BarChart3, title: 'Smart Demand Forecasting', badge: 'Predictive', c: 'var(--purple)',
    desc: 'Festival + macro + historical orders → predict surge/drop → auto-adjust reorder triggers.' 
  },
  { 
    icon: ShieldCheck, title: 'Human Authorization', badge: 'Limits', c: 'var(--cyan)',
    desc: 'Set spend limits (RM500), price caps (15%). High-risk actions request operator approval.' 
  },
  { 
    icon: FileText, title: 'Unstructured Ingestion', badge: '> 20%', c: 'var(--green)',
    desc: 'OCR + GLM-4V → extract items, detect price spikes (>20%) → trigger inventory debate.' 
  },
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
          
          {/* 2. 优化网格布局与卡片设计 */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(2, 1fr)', /* 强制 50/50 绝对对齐 */
            // 使用边框折叠思路：外层给顶部和左侧线
            borderTop: '1px solid var(--border-subtle)',
            borderLeft: '1px solid var(--border-subtle)',
            marginTop: 16
          }}>
            {F.map((f, i) => (
              <div key={i} style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                padding: '16px 12px',
                // 每个格子给右侧和底部线，形成完整的网格感
                borderRight: '1px solid var(--border-subtle)',
                borderBottom: '1px solid var(--border-subtle)',
                minHeight: '110px', /* 保证纵向也均匀 */
                boxSizing: 'border-box'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div style={{ 
                    padding: '5px', 
                    background: `${f.c}10`, 
                    border: `1px solid ${f.c}30`, 
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <f.icon size={14} color={f.c} />
                  </div>
                  {/* Badge 放在右上角，作为数据点暗示 */}
                  <span style={{ 
                    fontSize: 8, 
                    fontWeight: 700, 
                    color: f.c, 
                    opacity: 0.8,
                    letterSpacing: '0.5px',
                    fontFamily: 'var(--mono)'
                  }}>
                    {/* 之前建议的 Badge 数据 */}
                    {i === 0 ? '< 10S' : i === 1 ? '8D SENSE' : i === 2 ? 'SPIKE→PO' : i === 3 ? 'WEEKLY' : i === 4 ? 'RM500' : '> 20%'}
                  </span>
                </div>

                <div style={{ fontWeight: 600, fontSize: 11, color: 'var(--text-0)', marginBottom: 4 }}>
                  {f.title}
                </div>
                
                <div style={{ 
                  fontSize: 10, 
                  color: 'var(--text-2)', 
                  lineHeight: 1.5,
                  maxWidth: '100%' 
                }}>
                  {f.desc}
                </div>
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
