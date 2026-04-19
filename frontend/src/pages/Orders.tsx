import React from 'react';


const Orders: React.FC = () => {
  return (
    <div className="dashboard-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Kitchen & Floor Orders</h1>
          <p className="page-subtitle">Live KDS Queue & Status</p>
        </div>
      </header>

      <div className="card task-log-panel">
        <div className="card-header">
          <h3 className="card-title">Active Orders</h3>
          <span className="badge badge-gold">AI Resequenced</span>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order #</th>
                <th>Table/Source</th>
                <th>Items</th>
                <th>Status</th>
                <th>ETA</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>#1042</td>
                <td>Table 4 (VIP)</td>
                <td>2x Wagyu Bowl, 1x Truffle Fries</td>
                <td><span className="badge badge-gold">Cooking</span></td>
                <td>4 mins</td>
              </tr>
              <tr>
                <td>#1043</td>
                <td>Takeaway</td>
                <td>1x Salmon Roll</td>
                <td><span className="badge badge-blue">Prep</span></td>
                <td>8 mins</td>
              </tr>
              <tr>
                <td>#1041</td>
                <td>Table 12</td>
                <td>3x Chicken Bowl</td>
                <td><span className="badge badge-emerald">Ready</span></td>
                <td>-</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Orders;
