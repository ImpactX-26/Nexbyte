import React from 'react';

export default function QuarantineTable({ items, onResolve, onRefresh }) {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
            Quarantine Isolation Queue
          </h3>
          <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            {items.length} Isolated
          </span>
        </div>
        <button
          onClick={onRefresh}
          className="text-xs text-slate-400 hover:text-white transition"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
        {items.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4 text-center">
            No quarantined memories currently awaiting triage.
          </p>
        ) : (
          items.map((item) => {
            const m = item.memory;
            const sevColor =
              item.incident_severity === 'CRITICAL' ? 'text-rose-400 border-rose-500/40 bg-rose-500/10' :
              item.incident_severity === 'HIGH' ? 'text-orange-400 border-orange-500/40 bg-orange-500/10' :
              'text-amber-400 border-amber-500/40 bg-amber-500/10';

            return (
              <div key={m.id} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${sevColor}`}>
                    {item.incident_severity} SEVERITY
                  </span>
                  <span className="text-slate-400 font-mono text-[11px]">
                    Risk: {(m.evaluation.risk_score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs font-mono text-slate-200 bg-slate-900/80 p-2 rounded border border-slate-800/80">
                  {m.payload}
                </p>
                <div className="text-[11px] text-slate-400">
                  <p><strong>Reason:</strong> {m.evaluation.reason}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    Source: {m.source_type} &bull; User: {m.user_id}
                  </p>
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    onClick={() => onResolve(m.id, 'DELETE')}
                    className="px-3 py-1 rounded bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-600/40 text-xs font-semibold"
                  >
                    Purge
                  </button>
                  <button
                    onClick={() => onResolve(m.id, 'ALLOW')}
                    className="px-3 py-1 rounded bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-600/40 text-xs font-semibold"
                  >
                    Approve (ALLOW)
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
