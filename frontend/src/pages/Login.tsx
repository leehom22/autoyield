import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cpu, Lock, User, Briefcase, ChevronRight } from 'lucide-react';
import './Login.css';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [role, setRole] = useState<'Manager' | 'Staff'>('Manager');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate auth
    setTimeout(() => {
      setIsLoading(false);
      navigate(role === 'Manager' ? '/dashboard-manager' : '/dashboard-staff');
    }, 800);
  };

  return (
    <div className="login-container">
      <div className="login-visual">
        <div className="visual-overlay"></div>
        <div className="visual-content">
          <div className="brand-badge">Kernel v2.4 Active</div>
          <h1>Autonomous F&B<br />Operations Engine</h1>
          <p>Powered by Z.AI General Language Model</p>
          
          <div className="metrics-preview">
            <div className="metric-box">
              <span className="metric-value">+14.2%</span>
              <span className="metric-label">Margin Yield</span>
            </div>
            <div className="metric-box">
              <span className="metric-value">-21%</span>
              <span className="metric-label">Food Waste</span>
            </div>
            <div className="metric-box">
              <span className="metric-value">0.8s</span>
              <span className="metric-label">Agent Latency</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="login-form-wrapper">
        <div className="login-card glass-panel">
          <div className="login-header">
            <Cpu size={32} className="login-logo text-accent-gold" />
            <h2>AutoYield Access</h2>
            <p className="subtitle">Select your role to authenticate</p>
          </div>

          <div className="role-selector">
            <button 
              className={`role-btn ${role === 'Manager' ? 'active' : ''}`}
              onClick={() => setRole('Manager')}
              type="button"
            >
              <Briefcase size={20} />
              <span>Manager</span>
            </button>
            <button 
              className={`role-btn ${role === 'Staff' ? 'active' : ''}`}
              onClick={() => setRole('Staff')}
              type="button"
            >
              <User size={20} />
              <span>Staff</span>
            </button>
          </div>

          <form onSubmit={handleLogin} className="login-form">
            <div className="input-group">
              <label className="input-label">Access ID</label>
              <div className="input-with-icon">
                <User size={18} className="input-icon" />
                <input type="text" className="input-field" placeholder="Enter ID" defaultValue={role === 'Manager' ? 'admin' : 'staff'} />
              </div>
            </div>
            
            <div className="input-group">
              <label className="input-label">Security Key</label>
              <div className="input-with-icon">
                <Lock size={18} className="input-icon" />
                <input type="password" className="input-field" placeholder="••••••••" defaultValue="password" />
              </div>
            </div>

            <button type="submit" className="btn btn-primary login-submit" disabled={isLoading}>
              {isLoading ? (
                <span className="loading-spinner"></span>
              ) : (
                <>
                  Initialize Session <ChevronRight size={18} />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
