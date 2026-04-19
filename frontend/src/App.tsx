
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import ManagerDashboard from './pages/ManagerDashboard';
import StaffDashboard from './pages/StaffDashboard';
import AgentHub from './pages/AgentHub';
import GodMode from './pages/GodMode';
import Inventory from './pages/Inventory';
import Menu from './pages/Menu';
import Orders from './pages/Orders';
import Chatbot from './pages/Chatbot';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/login" replace />} />
          <Route path="dashboard-manager" element={<ManagerDashboard />} />
          <Route path="dashboard-staff" element={<StaffDashboard />} />
          <Route path="agent-hub" element={<AgentHub />} />
          <Route path="god-mode" element={<GodMode />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="menu" element={<Menu />} />
          <Route path="promotions" element={<Menu />} /> {/* Can be handled together or separate */}
          <Route path="orders" element={<Orders />} />
          <Route path="chatbot" element={<Chatbot />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
