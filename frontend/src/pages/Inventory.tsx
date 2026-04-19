import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Plus, Filter } from 'lucide-react';

const Inventory: React.FC = () => {
  const { role } = useOutletContext<{ role: string }>();
  const isManager = role === 'Manager';

  return (
    <div className="dashboard-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Inventory Management</h1>
          <p className="page-subtitle">Real-time stock levels and supplier pricing</p>
        </div>
        {isManager && (
          <div className="header-actions">
            <button className="btn btn-primary"><Plus size={18} /> Add Stock</button>
          </div>
        )}
      </header>

      <div className="card task-log-panel">
        <div className="card-header">
          <div className="topbar-search" style={{ width: '300px' }}>
            <Filter size={18} className="search-icon" />
            <input type="text" placeholder="Filter ingredients..." className="search-input" />
          </div>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ingredient</th>
                <th>Supplier</th>
                <th>Stock Level</th>
                <th>Unit Price</th>
                <th>Est. Depletion</th>
                {isManager && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Atlantic Salmon</td>
                <td>Oceanic Foods</td>
                <td><span className="badge badge-gold">14 kg (Low)</span></td>
                <td>$28.50/kg <span className="text-accent-red ml-2">↑ 18%</span></td>
                <td>1.2 days</td>
                {isManager && <td><button className="btn btn-secondary btn-sm">Edit</button></td>}
              </tr>
              <tr>
                <td>Wagyu Beef A4</td>
                <td>Prime Cuts Co.</td>
                <td><span className="badge badge-emerald">42 kg</span></td>
                <td>$85.00/kg</td>
                <td>6.4 days</td>
                {isManager && <td><button className="btn btn-secondary btn-sm">Edit</button></td>}
              </tr>
              <tr>
                <td>Premium Rice</td>
                <td>Grain Harvest</td>
                <td><span className="badge badge-emerald">120 kg</span></td>
                <td>$4.20/kg</td>
                <td>14 days</td>
                {isManager && <td><button className="btn btn-secondary btn-sm">Edit</button></td>}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Inventory;
