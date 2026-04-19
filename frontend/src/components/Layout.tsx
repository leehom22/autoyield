import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Cpu, 
  Zap, 
  Package, 
  Coffee, 
  ListOrdered, 
  MessageSquare,
  Bell,
  Search,
  User,
  ChevronRight
} from 'lucide-react';
import './Layout.css';

const Layout: React.FC = () => {
  const location = useLocation();
  const [role] = useState<'Manager' | 'Staff'>('Manager'); // Mock role

  const navItems = [
    { path: `/dashboard-${role.toLowerCase()}`, icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { path: '/agent-hub', icon: <Cpu size={20} />, label: 'Agent Hub', managerOnly: true },
    { path: '/inventory', icon: <Package size={20} />, label: 'Inventory' },
    { path: '/menu', icon: <Coffee size={20} />, label: 'Menu & Promo' },
    { path: '/orders', icon: <ListOrdered size={20} />, label: 'Orders' },
    { path: '/chatbot', icon: <MessageSquare size={20} />, label: 'Instruction Channel' },
    { path: '/god-mode', icon: <Zap size={20} />, label: 'God Mode (Demo)', className: 'text-accent-gold' },
  ];

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <Cpu className="logo-icon" size={24} />
            <span className="logo-text">AutoYield</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            if (item.managerOnly && role !== 'Manager') return null;
            
            return (
              <NavLink 
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''} ${item.className || ''}`}
              >
                {item.icon}
                <span className="nav-label">{item.label}</span>
                {location.pathname === item.path && <ChevronRight size={16} className="active-indicator" />}
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-indicator status-active"></span>
            <span className="status-text">Z.AI Kernel Online</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-content">
        {/* Top App Bar */}
        <header className="topbar">
          <div className="topbar-search">
            <Search size={18} className="search-icon" />
            <input type="text" placeholder="Search commands, orders, or inventory..." className="search-input" />
          </div>
          
          <div className="topbar-actions">
            <button className="icon-btn notification-btn">
              <Bell size={20} />
              <span className="notification-badge">3</span>
            </button>
            
            <div className="user-profile">
              <div className="user-info">
                <span className="user-name">Alex Chen</span>
                <span className="user-role badge badge-emerald">{role}</span>
              </div>
              <div className="user-avatar">
                <User size={20} />
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content animate-fade-in">
          <Outlet context={{ role }} />
        </main>
      </div>
    </div>
  );
};

export default Layout;
