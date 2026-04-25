import { useState } from 'react';
import { MOCK_WEEKLY_REPORT } from '../lib/mockData';
import ReactMarkdown from 'react-markdown';
import { TrendingUp, ShieldCheck, Zap } from 'lucide-react';

export default function WeeklyAnalysisReport() {
  const [report] = useState<any>(MOCK_WEEKLY_REPORT);

  return (
    <div style={{ padding: '12px 14px', overflow: 'auto', flex: 1 }}>
      <div className="panel panel-accent-green" style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
        <div className="panel-header" style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: 10 }}>
          <div className="row gap-8">
            <TrendingUp size={14} color="var(--green)" />
            <h3 style={{ fontSize: 13, fontWeight: 600 }}>Weekly Analysis Report</h3>
          </div>
          {report && (
            <span className="mono text-2" style={{ fontSize: 10, opacity: 0.8 }}>
              {new Date(report.timestamp).toLocaleString()}
            </span>
          )}
        </div>

        <div className="panel-body" style={{ marginTop: 12 }}>
          {!report ? (
            <div className="empty-state">No report available</div>
          ) : (
            <>
              {/* 1. Analysis (P-Agent vs R-Agent) */}
              {(report.p_agent_argument || report.r_agent_argument) && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                  <div style={{ background: 'var(--bg-base)', padding: '12px', borderRadius: 'var(--radius)', borderLeft: '3px solid var(--cyan)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, fontWeight: 700, color: 'var(--cyan)', textTransform: 'uppercase', marginBottom: 8 }}>
                      <Zap size={10} /> P-Agent Perspective
                    </div>
                    <div style={{ fontSize: 11.5, color: 'var(--text-1)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                      {report.p_agent_argument}
                    </div>
                  </div>
                  
                  <div style={{ background: 'var(--bg-base)', padding: '12px', borderRadius: 'var(--radius)', borderLeft: '3px solid var(--orange)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, fontWeight: 700, color: 'var(--orange)', textTransform: 'uppercase', marginBottom: 8 }}>
                      <ShieldCheck size={10} /> R-Agent Guardrail
                    </div>
                    <div style={{ fontSize: 11.5, color: 'var(--text-1)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                      {report.r_agent_argument}
                    </div>
                  </div>
                </div>
              )}

              {/* 2. Conclusion and Advice */}
              <div style={{ 
                background: 'linear-gradient(to bottom right, var(--bg-surface), var(--bg-base))', 
                padding: '16px', 
                borderRadius: '10px', 
                border: '1px solid var(--border-subtle)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)'
              }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--green)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: '0.5px' }}>
                  Final Summary & Actionable Insights
                </div>
                <div style={{ 
                  fontSize: '12.5px', 
                  color: 'var(--text-0)', 
                  lineHeight: 1.7,
                }} className="markdown-report">
                  <ReactMarkdown 
                    components={{
                      p: ({children}) => <p style={{ marginBottom: 10 }}>{children}</p>,
                      li: ({children}) => <li style={{ marginBottom: 6, marginLeft: 16 }}>{children}</li>,
                      strong: ({children}) => <strong style={{ color: 'var(--green)', fontWeight: 600 }}>{children}</strong>
                    }}
                  >
                    {report.action_taken}
                  </ReactMarkdown>
                </div>
              </div>

              {/* 3. Status bar */}
              {report.resolution && (
                <div style={{ marginTop: 12, padding: '4px 8px', borderRadius: 4, background: 'var(--bg-active)', display: 'inline-block' }}>
                  <span style={{ fontSize: 9, color: 'var(--text-2)', textTransform: 'uppercase', marginRight: 6 }}>Status:</span>
                  <span className="mono" style={{ fontSize: 10, color: 'var(--text-1)', fontWeight: 600 }}>{report.resolution}</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}