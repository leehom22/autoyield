import { useEffect, useState, useMemo } from 'react';
import { supabase } from '../lib/supabase';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';
//import { MOCK_MARKET_TRENDS } from '../lib/mockData';

interface TrendRecord {
  indicator: string;
  value: number;
  recorded_at: string;
}

export default function MacroTrendsChart() {
  const [raw, setRaw] = useState<TrendRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    const { data } = await supabase.from('market_trends_history').select('indicator, value, recorded_at').order('recorded_at', { ascending: true }).limit(30);
    setRaw(data || []);
    setLoading(false);
  };

  const chartData = useMemo(() => {
    const dateMap = new Map<string, Record<string, number>>();
    raw.forEach((r) => {
      const dateKey = new Date(r.recorded_at).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' });
      if (!dateMap.has(dateKey)) dateMap.set(dateKey, { date: dateKey } as any);
      const entry = dateMap.get(dateKey)!;
      (entry as any)[r.indicator] = r.value;
    });
    return Array.from(dateMap.values());
  }, [raw]);

  const isEmpty = !loading && chartData.length === 0;

  return (
    <div style={{ padding: '10px 12px' }}>
      <div className="row" style={{ marginBottom: 8, justifyContent: 'space-between' }}>
        <div className="row gap-4">
          <TrendingUp size={13} color="var(--cyan)" />
          <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.3px', color: 'var(--text-1)' }}>
            Macro Trends
          </span>
        </div>
        <span className="badge badge-cyan" style={{ fontSize: 9 }}>
          <BarChart3 size={9} /> Last 30 Records
        </span>
      </div>

      {loading && (
        <div className="empty-state" style={{ padding: '30px 0' }}>
          <span className="pulse" style={{ color: 'var(--cyan)' }}>Loading trends…</span>
        </div>
      )}

      {isEmpty && (
        <div className="empty-state" style={{ padding: '30px 0' }}>
          <BarChart3 size={20} style={{ marginBottom: 6, opacity: 0.4 }} />
          <div>No trend data available</div>
        </div>
      )}

      {!loading && !isEmpty && (
        <div style={{
          background: 'var(--glass)',
          border: '1px solid var(--glass-border)',
          borderRadius: 'var(--radius)',
          padding: '10px 6px 4px 0',
        }}>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-2)', fontSize: 9, fontFamily: 'var(--mono)' }}
                axisLine={{ stroke: 'var(--border)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: 'var(--text-2)', fontSize: 9, fontFamily: 'var(--mono)' }}
                axisLine={false}
                tickLine={false}
                width={40}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  fontSize: 10,
                  fontFamily: 'var(--font)',
                  color: 'var(--text-0)',
                  boxShadow: '0 4px 16px rgba(0,0,0,.5)',
                }}
                itemStyle={{ padding: '1px 0' }}
                labelStyle={{ color: 'var(--text-1)', fontSize: 10, marginBottom: 4 }}
              />
              <Legend
                iconType="circle"
                iconSize={6}
                wrapperStyle={{ fontSize: 10, fontFamily: 'var(--font)', color: 'var(--text-1)', paddingTop: 4 }}
              />
              <Line
                type="monotone"
                dataKey="oil_price"
                name="Oil Price"
                stroke="var(--orange)"
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3, fill: 'var(--orange)' }}
              />
              <Line
                type="monotone"
                dataKey="usd_myr"
                name="USD/MYR"
                stroke="var(--cyan)"
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3, fill: 'var(--cyan)' }}
              />
              <Line
                type="monotone"
                dataKey="local_inflation"
                name="Inflation"
                stroke="var(--purple)"
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3, fill: 'var(--purple)' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
