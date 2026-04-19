import React, { useState, useEffect, useRef } from 'react';
import { Zap, Terminal, TrendingUp, AlertOctagon, Activity, Play, ArrowRight } from 'lucide-react';
import './GodMode.css';

interface Trace {
  id: string;
  timestamp: string;
  text: string;
  type: 'info' | 'warning' | 'action' | 'thought';
}

const GodMode: React.FC = () => {
  const [activeCrisis, setActiveCrisis] = useState<string | null>(null);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const traceEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll traces
  useEffect(() => {
    traceEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [traces]);

  const triggerCrisis = (type: string) => {
    setActiveCrisis(type);
    setIsSimulating(true);
    setTraces([{
      id: Date.now().toString(),
      timestamp: new Date().toLocaleTimeString(),
      text: `SYSTEM INJECTION: [${type}] initiated by Judge.`,
      type: 'warning'
    }]);

    // Simulate SSE / Agent Reasoning
    const simulationSteps = [
      { delay: 1000, text: "GLM Wakeup: Detecting anomaly in state...", type: "info" },
      { delay: 2500, text: "Context Parsing: Analyzing current inventory vs active orders...", type: "thought" },
      { delay: 4000, text: "Risk Assessment: Margin collapse imminent within 2.4 hours if unmitigated.", type: "warning" },
      { delay: 6000, text: "Strategy Generation: Formulating multi-variable optimization (Margin vs Stock vs Demand)...", type: "thought" },
      { delay: 8000, text: "P-Agent Proposal: Substitution required. Calculating alternatives for affected ingredients...", type: "thought" },
      { delay: 10500, text: "R-Agent Execution: Dynamically rewriting active menu to suppress affected items.", type: "action" },
      { delay: 12000, text: "API Call: Updating KDS (Kitchen Display System) routing priorities.", type: "action" },
      { delay: 14000, text: "System State Restored. Crisis Mitigation complete. Awaiting Manager Approval for permanent supplier swap.", type: "info" }
    ] as const;

    simulationSteps.forEach(step => {
      setTimeout(() => {
        setTraces(prev => [...prev, {
          id: Date.now().toString(),
          timestamp: new Date().toLocaleTimeString(),
          text: step.text,
          type: step.type
        }]);
        if (step.delay === 14000) setIsSimulating(false);
      }, step.delay);
    });
  };

  return (
    <div className="god-mode-container">
      <header className="page-header god-mode-header">
        <div>
          <h1 className="page-title text-accent-gold"><Zap className="inline-icon" /> Judge Sandbox</h1>
          <p className="page-subtitle">Inject crises to test Z.AI GLM autonomous recovery</p>
        </div>
      </header>

      <div className="god-mode-grid">
        {/* Left Column: Controls & Traces */}
        <div className="god-mode-left">
          
          <div className="card crisis-panel">
            <div className="card-header">
              <h3 className="card-title">Crisis Injection Matrix</h3>
            </div>
            <div className="crisis-buttons">
              <button 
                className={`btn crisis-btn ${activeCrisis === 'inventory' ? 'active' : ''}`}
                onClick={() => triggerCrisis('inventory')}
                disabled={isSimulating}
              >
                <AlertOctagon size={24} className="crisis-icon" />
                <div className="crisis-info">
                  <h4>Slash Inventory 50%</h4>
                  <p>Triggers sudden shortage of core ingredient</p>
                </div>
                <Play size={16} />
              </button>

              <button 
                className={`btn crisis-btn ${activeCrisis === 'cost' ? 'active' : ''}`}
                onClick={() => triggerCrisis('cost')}
                disabled={isSimulating}
              >
                <TrendingUp size={24} className="crisis-icon" />
                <div className="crisis-info">
                  <h4>Spike Supplier Cost</h4>
                  <p>Triggers margin preservation protocol</p>
                </div>
                <Play size={16} />
              </button>

              <button 
                className={`btn crisis-btn ${activeCrisis === 'demand' ? 'active' : ''}`}
                onClick={() => triggerCrisis('demand')}
                disabled={isSimulating}
              >
                <Activity size={24} className="crisis-icon" />
                <div className="crisis-info">
                  <h4>Demand Surge (VIP)</h4>
                  <p>Triggers kitchen re-sequencing & ETAs</p>
                </div>
                <Play size={16} />
              </button>
            </div>
          </div>

          <div className="card terminal-card glass-panel">
            <div className="terminal-header">
              <Terminal size={18} />
              <span>GLM Live Thought Trace</span>
              {isSimulating && <span className="status-indicator status-active ml-auto"></span>}
            </div>
            <div className="terminal-body">
              {traces.length === 0 ? (
                <div className="terminal-empty">Awaiting injection... System nominal.</div>
              ) : (
                traces.map((trace) => (
                  <div key={trace.id} className={`trace-line type-${trace.type} animate-fade-in`}>
                    <span className="trace-time">[{trace.timestamp}]</span>
                    <span className="trace-text">{trace.text}</span>
                  </div>
                ))
              )}
              <div ref={traceEndRef} />
            </div>
          </div>

        </div>

        {/* Right Column: Live Reactions */}
        <div className="god-mode-right">
          <div className="card reaction-panel">
            <div className="card-header">
              <h3 className="card-title">Live Menu Reactivity</h3>
              <span className="badge badge-emerald">Real-time Sync</span>
            </div>
            
            <div className="menu-comparison">
              <div className="menu-state">
                <h4>Before Crisis</h4>
                <div className="menu-items">
                  <div className="menu-item active">
                    <span className="item-name">Signature Salmon Roll</span>
                    <span className="item-price">$18.00</span>
                  </div>
                  <div className="menu-item active">
                    <span className="item-name">Wagyu Beef Bowl</span>
                    <span className="item-price">$24.00</span>
                  </div>
                  <div className="menu-item active">
                    <span className="item-name">Truffle Fries</span>
                    <span className="item-price">$12.00</span>
                  </div>
                </div>
              </div>
              
              <div className="comparison-arrow">
                <ArrowRight size={24} className={isSimulating ? 'text-accent-gold' : 'text-muted'} />
              </div>

              <div className="menu-state">
                <h4>After Mitigation</h4>
                <div className="menu-items">
                  <div className={`menu-item ${activeCrisis === 'cost' ? 'modified' : 'active'}`}>
                    <span className="item-name">Signature Salmon Roll</span>
                    <span className="item-price">{activeCrisis === 'cost' ? '$21.50' : '$18.00'}</span>
                    {activeCrisis === 'cost' && <span className="item-tag">Auto-Repriced</span>}
                  </div>
                  <div className={`menu-item ${activeCrisis === 'inventory' ? 'disabled' : 'active'}`}>
                    <span className="item-name">Wagyu Beef Bowl</span>
                    <span className="item-price">$24.00</span>
                    {activeCrisis === 'inventory' && <span className="item-tag danger">Out of Stock</span>}
                  </div>
                  <div className={`menu-item active ${activeCrisis === 'inventory' ? 'promoted' : ''}`}>
                    <span className="item-name">Chicken Truffle Bowl</span>
                    <span className="item-price">$18.00</span>
                    {activeCrisis === 'inventory' && <span className="item-tag success">Alternative</span>}
                  </div>
                </div>
              </div>
            </div>
            
            {activeCrisis && !isSimulating && (
              <div className="mitigation-summary animate-fade-in">
                <h4>GLM Optimization Result:</h4>
                <p>Profit margin preserved within 1.2% variance. KDS updated. 0 human intervention required.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GodMode;
