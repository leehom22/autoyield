import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Edit2 } from 'lucide-react';

const Menu: React.FC = () => {
  const { role } = useOutletContext<{ role: string }>();
  const isManager = role === 'Manager';

  return (
    <div className="dashboard-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Menu & Offerings</h1>
          <p className="page-subtitle">Active menu items and margin calculations</p>
        </div>
      </header>

      <div className="dashboard-grid">
        <div className="card task-log-panel span-full">
          <div className="card-header">
            <h3 className="card-title">Active Menu</h3>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Dish Name</th>
                  <th>Core Ingredients</th>
                  <th>Retail Price</th>
                  <th>Est. Margin</th>
                  <th>Status</th>
                  {isManager && <th>Action</th>}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Signature Salmon Roll</td>
                  <td>Atlantic Salmon, Rice, Nori</td>
                  <td>$18.00</td>
                  <td><span className="text-accent-red">42% (Warning)</span></td>
                  <td><span className="badge badge-emerald">Active</span></td>
                  {isManager && <td><button className="btn btn-secondary btn-sm"><Edit2 size={14} /></button></td>}
                </tr>
                <tr>
                  <td>Wagyu Beef Bowl</td>
                  <td>Wagyu Beef A4, Rice, Onions</td>
                  <td>$24.00</td>
                  <td>68%</td>
                  <td><span className="badge badge-emerald">Active</span></td>
                  {isManager && <td><button className="btn btn-secondary btn-sm"><Edit2 size={14} /></button></td>}
                </tr>
                <tr>
                  <td>Chicken Truffle Bowl</td>
                  <td>Chicken, Truffle Oil, Rice</td>
                  <td>$18.00</td>
                  <td>75%</td>
                  <td><span className="badge badge-blue">Boosted</span></td>
                  {isManager && <td><button className="btn btn-secondary btn-sm"><Edit2 size={14} /></button></td>}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Menu;
