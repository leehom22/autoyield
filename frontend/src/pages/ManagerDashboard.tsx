import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Activity, CheckCircle2 } from 'lucide-react';
import './ManagerDashboard.css';

const ManagerDashboard: React.FC = () => {
  return (
    <div className="dashboard-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Executive Overview</h1>
          <p className="page-subtitle">Real-time performance and Z.AI insights</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary">Download Report</button>
          <button className="btn btn-primary">Refresh Data</button>
        </div>
      </header>

      {/* KPI Cards */}
      <section className="kpi-grid">
        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Gross Revenue</span>
            <Activity size={18} className="text-accent-blue" />
          </div>
          <div className="kpi-value">$24,592.00</div>
          <div className="kpi-trend positive">
            <TrendingUp size={16} />
            <span>+12.5% vs yesterday</span>
          </div>
        </div>
        
        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Food Waste Rate</span>
            <TrendingDown size={18} className="text-accent-emerald" />
          </div>
          <div className="kpi-value">2.4%</div>
          <div className="kpi-trend positive">
            <TrendingDown size={16} />
            <span>-1.2% optimal</span>
          </div>
        </div>
        
        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Agent Interventions</span>
            <CheckCircle2 size={18} className="text-accent-gold" />
          </div>
          <div className="kpi-value">14</div>
          <div className="kpi-trend neutral">
            <span>Past 24 hours</span>
          </div>
        </div>
      </section>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Alerts & Anomalies */}
        <div className="card anomalies-card">
          <div className="card-header">
            <h3 className="card-title">System Alerts</h3>
            <span className="badge badge-red">2 Critical</span>
          </div>
          <div className="alerts-list">
            <div className="alert-item critical">
              <AlertTriangle size={18} className="alert-icon" />
              <div className="alert-content">
                <h4>Price Spike Detected: Atlantic Salmon</h4>
                <p>Supplier 'Oceanic Foods' increased price by 18%. P-Agent holding substitution proposal.</p>
              </div>
              <button className="btn btn-secondary btn-sm">Review</button>
            </div>
            <div className="alert-item warning">
              <Activity size={18} className="alert-icon text-accent-gold" />
              <div className="alert-content">
                <h4>Inventory Warning: Premium Rice</h4>
                <p>Stock depleting 40% faster than historical average. 0.8 days remaining.</p>
              </div>
              <button className="btn btn-secondary btn-sm">Review</button>
            </div>
          </div>
        </div>

        {/* Agent Decisions Summary */}
        <div className="card agent-summary-card">
          <div className="card-header">
            <h3 className="card-title">Recent Z.AI Actions</h3>
            <span className="badge badge-emerald">R-Agent Active</span>
          </div>
          <div className="decisions-list">
            <div className="decision-item">
              <div className="decision-time">10:42 AM</div>
              <div className="decision-details">
                <p className="decision-text">Autonomously re-sequenced kitchen orders to prioritize 3 high-value VIP tables. Estimated wait time reduced by 4 mins.</p>
                <div className="decision-tags">
                  <span className="tag">Kitchen Ops</span>
                  <span className="tag success">Executed</span>
                </div>
              </div>
            </div>
            <div className="decision-item">
              <div className="decision-time">09:15 AM</div>
              <div className="decision-details">
                <p className="decision-text">Detected 12°C temperature drop in weather forecast. Proactively boosted visibility of hot soups & stews on digital menu.</p>
                <div className="decision-tags">
                  <span className="tag">Menu Optimization</span>
                  <span className="tag success">Executed</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManagerDashboard;
