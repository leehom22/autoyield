import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { ClipboardList, Plus, Truck } from 'lucide-react';
//import { MOCK_PROCUREMENT_LOGS } from '../lib/mockData';

interface ProcurementLog {
  id: string;
  ingredient_name?: string;
  supplier_name?: string;
  quantity: number;
  unit_price: number;
  status: string;
  estimated_arrival: string | null;
  created_at: string;
  inventory?: { name: string } | null;
  suppliers?: { name: string } | null;
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'badge-orange',
  ordered: 'badge-cyan',
  shipped: 'badge-purple',
  delivered: 'badge-green',
  cancelled: 'badge-red',
};

export default function ProcurementLogs() {
  const [logs, setLogs] = useState<ProcurementLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();

    const channel = supabase
      .channel('procurement-realtime')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'procurement_logs' }, () => {
        fetchLogs();
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  // useEffect(() => {
  //   fetchLogs();

  //   const channel = supabase
  //     .channel('procurement-realtime')
  //     .on(
  //       'postgres_changes',
  //       { event: 'INSERT', schema: 'public', table: 'procurement_logs' },
  //       async (payload) => {
  //         const newRow = payload.new as any;
  //         // Try to get ingredient & supplier names
  //         let ingredientName = newRow.ingredient_name || '—';
  //         let supplierName = newRow.supplier_name || '—';
  //         if (newRow.inventory_id) {
  //           const { data: inv } = await supabase.from('inventory').select('name').eq('id', newRow.inventory_id).single();
  //           if (inv) ingredientName = inv.name;
  //         }
  //         if (newRow.supplier_id) {
  //           const { data: sup } = await supabase.from('suppliers').select('name').eq('id', newRow.supplier_id).single();
  //           if (sup) supplierName = sup.name;
  //         }
  //         setLogs((prev) => [{
  //           ...newRow,
  //           ingredient_name: ingredientName,
  //           supplier_name: supplierName,
  //         }, ...prev]);
  //       }
  //     )
  //     .subscribe();

  //   return () => { supabase.removeChannel(channel); };
  // }, []);

  const fetchLogs = async () => {
    setLoading(true);
    const { data } = await supabase
    .from('procurement_logs')
    .select(`
      *,
      inventory:item_id (name),
      suppliers:supplier_id (name)
    `)
    .order('created_at', { ascending: false })
    .limit(20);

    if (data && data.length > 0) {
      const mappedLogs: ProcurementLog[] = data.map((item: any) => ({
        id: item.id,
        quantity: item.qty,
        unit_price: item.unit_cost,
        status: item.delivery_status,
        estimated_arrival: item.arrival_estimate,
        created_at: item.created_at,
        ingredient_name: item.inventory?.name,
        supplier_name: item.suppliers?.name,
        inventory: item.inventory,
        suppliers: item.suppliers,
      }));
      setLogs(mappedLogs);
    } else {
      setLogs([]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <div className="row" style={{ padding: '10px 12px', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div className="row gap-4">
          <ClipboardList size={13} color="var(--green)" />
          <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.3px', color: 'var(--text-1)' }}>
            Procurement Logs
          </span>
          <span className="badge badge-green" style={{ fontSize: 9 }}>
            <Plus size={8} /> Realtime
          </span>
        </div>
        <span className="text-2" style={{ fontSize: 10 }}>{logs.length} records</span>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading ? (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <span className="pulse" style={{ color: 'var(--green)' }}>Loading procurement data…</span>
          </div>
        ) : logs.length === 0 ? (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <Truck size={20} style={{ marginBottom: 6, opacity: 0.4 }} />
            <div>No procurement logs yet</div>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Ingredient</th>
                <th>Supplier</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Unit Price</th>
                <th className="text-right">Total</th>
                <th>Status</th>
                <th>ETA</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="slide-in">
                  <td className="truncate" style={{ maxWidth: 120 }}>{log.ingredient_name}</td>
                  <td className="truncate" style={{ maxWidth: 110 }}>{log.supplier_name}</td>
                  <td className="text-right mono">{log.quantity}</td>
                  <td className="text-right mono">${log.unit_price?.toFixed(2)}</td>
                  <td className="text-right mono text-cyan">${(log.quantity * log.unit_price).toFixed(2)}</td>
                  <td>
                    <span className={`badge ${STATUS_STYLES[log.status] || 'badge-cyan'}`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="mono text-2" style={{ fontSize: 10 }}>
                    {log.estimated_arrival ? new Date(log.estimated_arrival).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
