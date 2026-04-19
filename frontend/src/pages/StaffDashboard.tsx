import React from 'react';
import { Package, ListOrdered, Coffee } from 'lucide-react';

const StaffDashboard: React.FC = () => {
  return (
    <div className="dashboard-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Shift Overview</h1>
          <p className="page-subtitle">Current metrics and system status</p>
        </div>
      </header>

      <section className="kpi-grid">
        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Orders Handled</span>
            <ListOrdered size={18} className="text-accent-blue" />
          </div>
          <div className="kpi-value">42</div>
          <div className="kpi-trend neutral"><span>This shift</span></div>
        </div>
        
        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Active Items</span>
            <Coffee size={18} className="text-accent-emerald" />
          </div>
          <div className="kpi-value">28</div>
          <div className="kpi-trend neutral"><span>Live on Menu</span></div>
        </div>
        
        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Inventory Alerts</span>
            <Package size={18} className="text-accent-gold" />
          </div>
          <div className="kpi-value">1</div>
          <div className="kpi-trend negative"><span>Low stock</span></div>
        </div>
      </section>
      
      <div className="card mt-4">
        <h3 className="mb-4">Recent AI Instructions</h3>
        <p className="text-muted">The system recently re-sequenced kitchen orders to optimize flow. Please follow the updated KDS display.</p>
      </div>
    </div>
  );
};

export default StaffDashboard;
