import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { MOCK_WEEKLY_REPORT } from '../lib/mockData';

export default function WeeklyAnalysisReport() {
  const [report, setReport] = useState<any>(MOCK_WEEKLY_REPORT);

  useEffect(() => {
    supabase.from('decision_logs').select('*').eq('trigger_signal', 'WEEKLY_FORECAST').order('timestamp', { ascending: false }).limit(1)
      .then(({ data }) => { if (data?.length) setReport(data[0]); });
  }, []);

  return (
    <div style={{ padding: '12px 14px', overflow: 'auto', flex: 1 }}>
      <div className="panel panel-accent-green">
        <div className="panel-header"><h3>Weekly Analysis Report</h3>{report && <span className="mono text-2" style={{ fontSize: 10 }}>{new Date(report.timestamp).toLocaleString()}</span>}</div>
        <div className="panel-body">
          {!report ? <div className="empty-state">No report available</div> : (
            <>
              {(report.p_agent_argument || report.r_agent_argument) && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
                  <div style={{ background: 'var(--bg-base)', padding: '8px 10px', borderRadius: 'var(--radius)', borderLeft: '2px solid var(--cyan)' }}>
                    <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--cyan)', textTransform: 'uppercase', marginBottom: 4 }}>P-Agent Analysis</div>
                    <div style={{ fontSize: 11, color: 'var(--text-1)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{report.p_agent_argument}</div>
                  </div>
                  <div style={{ background: 'var(--bg-base)', padding: '8px 10px', borderRadius: 'var(--radius)', borderLeft: '2px solid var(--orange)' }}>
                    <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--orange)', textTransform: 'uppercase', marginBottom: 4 }}>R-Agent Analysis</div>
                    <div style={{ fontSize: 11, color: 'var(--text-1)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{report.r_agent_argument}</div>
                  </div>
                </div>
              )}
              <div style={{ background: 'var(--bg-base)', padding: '10px 12px', borderRadius: 'var(--radius)', borderLeft: '2px solid var(--green)' }}>
                <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--green)', textTransform: 'uppercase', marginBottom: 6 }}>Summary & Recommendations</div>
                <div style={{ fontSize: 12, color: 'var(--text-0)', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>{report.action_taken}</div>
              </div>
              {report.resolution && <div style={{ marginTop: 8, fontSize: 10, color: 'var(--text-2)' }}>Resolution: {report.resolution}</div>}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
