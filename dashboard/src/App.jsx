import React, { useState, useEffect } from 'react';
import TelemetryCards from './components/TelemetryCards';
import IngestSandbox from './components/IngestSandbox';
import QuarantineTable from './components/QuarantineTable';
import AuditTrail from './components/AuditTrail';

export default function App() {
  const [stats, setStats] = useState(null);
  const [quarantineItems, setQuarantineItems] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [retrievalQuery, setRetrievalQuery] = useState('');
  const [retrievalResult, setRetrievalResult] = useState('');

  const fetchStats = async () => {
    try {
      const res = await fetch('/v1/dashboard/stats');
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchQuarantine = async () => {
    try {
      const res = await fetch('/v1/quarantine');
      const data = await res.json();
      setQuarantineItems(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAudit = async () => {
    try {
      const res = await fetch('/v1/audit/logs?limit=20');
      const data = await res.json();
      setAuditLogs(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleResolveQuarantine = async (id, action) => {
    const notes = prompt(`Analyst remediation note for ${action}:`, `Analyst manual ${action.toLowerCase()} override.`);
    if (notes === null) return;
    try {
      await fetch(`/v1/quarantine/${id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          analyst_id: 'SOC_ANALYST_01',
          notes,
        }),
      });
      refreshAll();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleRetrieve = async () => {
    try {
      const res = await fetch('/v1/memory/retrieve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: retrievalQuery || 'preferences',
          user_id: 'user_samarth',
          top_k: 5,
        }),
      });
      const data = await res.json();
      setRetrievalResult(
        `Returned: ${data.returned_count} safe items (Quarantined Filtered: ${data.quarantined_filtered_count})\n\n${data.safe_context_str}`
      );
    } catch (e) {
      setRetrievalResult('Retrieval error: ' + e.message);
    }
  };

  const refreshAll = () => {
    fetchStats();
    fetchQuarantine();
    fetchAudit();
  };

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center text-slate-950 font-black text-xl shadow-lg shadow-emerald-500/20">
            🛡️
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              NexByte MemoryShield
            </h1>
            <p className="text-xs text-slate-400">AI Long-Term Memory & RAG Security Gateway</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
          >
            OpenAPI Docs
          </a>
          <span className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 font-medium">
            Active Protection
          </span>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6 flex-1 w-full">
        <TelemetryCards stats={stats} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 space-y-6">
            <IngestSandbox onIngestSuccess={refreshAll} />

            {/* Retrieval sandbox */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-2">
                Safe Context Retrieval
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={retrievalQuery}
                  onChange={(e) => setRetrievalQuery(e.target.value)}
                  placeholder="Query (e.g. 'coding preferences')"
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:border-cyan-500 focus:outline-none"
                />
                <button
                  onClick={handleRetrieve}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded-lg text-xs"
                >
                  Retrieve
                </button>
              </div>
              {retrievalResult && (
                <pre className="mt-3 p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {retrievalResult}
                </pre>
              )}
            </div>
          </div>

          <div className="lg:col-span-7 space-y-6">
            <QuarantineTable
              items={quarantineItems}
              onResolve={handleResolveQuarantine}
              onRefresh={fetchQuarantine}
            />
            <AuditTrail logs={auditLogs} onRefresh={fetchAudit} />
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
        NexByte MemoryShield &bull; Active AI Memory Defense &bull; Production Security Gateway
      </footer>
    </div>
  );
}
