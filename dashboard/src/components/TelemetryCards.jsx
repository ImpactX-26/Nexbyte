import React from 'react';

export default function TelemetryCards({ stats }) {
  if (!stats) return null;

  const cards = [
    { label: 'Total Ingested', val: stats.total_ingested, color: 'text-white', border: 'border-slate-800' },
    { label: 'Active (Safe)', val: stats.total_active, color: 'text-emerald-400', border: 'border-emerald-900/40' },
    { label: 'Under Review', val: stats.total_under_review, color: 'text-amber-400', border: 'border-amber-900/40' },
    { label: 'Quarantined', val: stats.total_quarantined, color: 'text-rose-400', border: 'border-rose-900/40' },
    { label: 'Threats Blocked', val: stats.threats_prevented_count, color: 'text-purple-400', border: 'border-purple-900/40' },
    { label: 'Avg Risk Score', val: `${(stats.avg_risk_score * 100).toFixed(1)}%`, color: 'text-cyan-400', border: 'border-cyan-900/40' },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((c, idx) => (
        <div key={idx} className={`p-4 rounded-xl bg-slate-900 border ${c.border} transition hover:border-slate-700`}>
          <p className="text-xs text-slate-400 font-medium">{c.label}</p>
          <p className={`text-2xl font-bold ${c.color} mt-1`}>{c.val}</p>
        </div>
      ))}
    </div>
  );
}
