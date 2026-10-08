import React from 'react';

export default function AuditTrail({ logs, onRefresh }) {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
          Immutable SOC Audit Trail
        </h3>
        <button
          onClick={onRefresh}
          className="text-xs text-slate-400 hover:text-white transition"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-2 max-h-72 overflow-y-auto font-mono text-[11px] pr-1">
        {logs.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-2 text-center">
            No audit records logged yet.
          </p>
        ) : (
          logs.map((l) => {
            const actionColor =
              l.event_type === 'QUARANTINE' ? 'text-rose-400' :
              l.event_type === 'ANALYST_OVERRIDE' ? 'text-cyan-400' :
              l.event_type === 'RETRIEVE' ? 'text-blue-400' :
              'text-emerald-400';

            const time = new Date(l.timestamp).toLocaleTimeString();

            return (
              <div
                key={l.id}
                className="p-2 rounded bg-slate-950/60 border border-slate-900 flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="text-slate-500">[{time}]</span>
                  <span className={`font-bold ${actionColor}`}>{l.event_type}</span>
                  <span className="text-slate-400">{l.action_taken} ({l.user_id})</span>
                </div>
                <span className="text-slate-500">
                  Risk: {(l.risk_score * 100).toFixed(0)}%
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
