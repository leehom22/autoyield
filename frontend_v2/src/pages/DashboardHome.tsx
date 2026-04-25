import { useOutletContext } from 'react-router-dom';
import type { Tab } from '../components/Layout/DashboardLayout';
import GodModeConsole from '../components/GodModeConsole';
import OrderQueueVisualizer from '../components/OrderQueueVisualizer';
import BusinessDashboard from '../components/BusinessDashboard';
import ChatbotPanel from '../components/ChatbotPanel';
import InvoiceImportPanel from '../components/InvoiceImportPanel';
import WeeklyAnalysisReport from '../components/WeeklyAnalysisReport';

export default function DashboardHome() {
  const { activeTab, sseState } = useOutletContext<{ activeTab: Tab; sseState: any }>();

  if (activeTab === 'sandbox') {
    return (
      <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
        <div className="flex-col" style={{ flex: '0 0 55%', borderRight: '1px solid var(--border)', overflow: 'hidden' }}>
          <GodModeConsole />
        </div>
        <div className="flex-col" style={{ flex: 1, overflow: 'hidden' }}>
          <OrderQueueVisualizer sseState={sseState} />
        </div>
      </div>
    );
  }
  if (activeTab === 'operations') return <BusinessDashboard />;
  if (activeTab === 'agent-io') {
    return (
      <div style={{ display: 'flex', height: '100%', overflow: 'hidden', gap: 0 }}>
        <div className="flex-col" style={{ flex: 1, minWidth: 0 }}>
          <ChatbotPanel />
        </div>
        <div className="flex-col" style={{ flex: 1, minWidth: 0, borderLeft: '1px solid var(--border)' }}>
          <InvoiceImportPanel />
        </div>
      </div>
    );
  }
  if (activeTab === 'report') return <WeeklyAnalysisReport />;
  return null;
}
