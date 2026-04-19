import React from 'react';
import { ShieldAlert, Check, X, FileSearch } from 'lucide-react';
import './AgentHub.css';

const AgentHub: React.FC = () => {
  return (
    <div className="agent-hub-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Z.AI Control Center</h1>
          <p className="page-subtitle">Monitor and authorize AI-generated proposals</p>
        </div>
      </header>

      <div className="agent-hub-grid">
        {/* Authorization Panel */}
        <div className="card auth-panel border-accent-gold">
          <div className="card-header">
            <h3 className="card-title text-accent-gold">
              <ShieldAlert className="inline-icon" /> P-Agent Authorization Queue
            </h3>
            <span className="badge badge-gold">1 Pending</span>
          </div>
          
          <div className="auth-card">
            <div className="auth-card-header">
              <h4>Proposed Action: Change Primary Salmon Supplier</h4>
              <span className="confidence-badge">High Confidence: 94%</span>
            </div>
            <div className="auth-card-body">
              <p className="reasoning">
                <strong>Trigger:</strong> 'Oceanic Foods' increased prices by 18% (Anomaly Detected).<br/>
                <strong>Proposal:</strong> Switch to 'Pacific Catch'. <br/>
                <strong>Impact:</strong> Recovers 15% margin drop, maintains existing delivery schedule.
              </p>
              <div className="auth-actions">
                <button className="btn btn-success"><Check size={18} /> Approve</button>
                <button className="btn btn-danger"><X size={18} /> Deny</button>
                <button className="btn btn-secondary"><FileSearch size={18} /> View Full Trace</button>
              </div>
            </div>
          </div>
        </div>

        {/* Suggestion Panel */}
        <div className="card suggestion-panel">
          <div className="card-header">
            <h3 className="card-title">Agent Suggestions</h3>
            <span className="badge badge-blue">R-Agent</span>
          </div>
          <ul className="suggestion-list">
            <li>
              <div className="suggestion-content">
                <strong>Menu Optimization:</strong> Consider removing 'Avocado Toast' for the next 2 days due to supply chain delays.
              </div>
              <span className="suggestion-confidence">88%</span>
            </li>
            <li>
              <div className="suggestion-content">
                <strong>Promotion Alert:</strong> Launch 15% Flash Sale on 'Cold Brew' between 2-4 PM to clear excess inventory.
              </div>
              <span className="suggestion-confidence">91%</span>
            </li>
          </ul>
        </div>

        {/* Agent Task Log Table */}
        <div className="card task-log-panel span-full">
          <div className="card-header">
            <h3 className="card-title">Agent Task Log</h3>
            <button className="btn btn-secondary btn-sm">Export Logs</button>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Agent Role</th>
                  <th>Decision Summary</th>
                  <th>Status</th>
                  <th>Trace Preview</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>10:42 AM</td>
                  <td><span className="badge badge-blue">R-Agent</span></td>
                  <td>Kitchen Re-sequencing</td>
                  <td><span className="badge badge-emerald">Executed</span></td>
                  <td className="trace-cell"><code>{`{ "priority": "VIP", "ETA_adjust": "-4m" }`}</code></td>
                </tr>
                <tr>
                  <td>09:15 AM</td>
                  <td><span className="badge badge-blue">R-Agent</span></td>
                  <td>Weather-based Menu Boost</td>
                  <td><span className="badge badge-emerald">Executed</span></td>
                  <td className="trace-cell"><code>{`{ "temp_drop": true, "boost": "soups" }`}</code></td>
                </tr>
                <tr>
                  <td>08:00 AM</td>
                  <td><span className="badge badge-gold">P-Agent</span></td>
                  <td>Supplier Switch Proposal</td>
                  <td><span className="badge badge-gold">Awaiting Auth</span></td>
                  <td className="trace-cell"><code>{`{ "trigger": "price_spike", "target": "salmon" }`}</code></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentHub;
