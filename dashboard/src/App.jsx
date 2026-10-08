import React, { useState, useEffect } from 'react';
import TelemetryCards from './components/TelemetryCards';
import IngestSandbox from './components/IngestSandbox';
import QuarantineTable from './components/QuarantineTable';
import AuditTrail from './components/AuditTrail';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
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
      const res = await fetch('/v1/audit/logs?limit=30');
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-black">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('home')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center text-slate-950 font-black text-xl shadow-lg shadow-emerald-500/20">
            🛡️
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                NexByte MemoryShield
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
                v1.0 ACTIVE
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Zero-Trust AI Long-Term Memory & RAG Security Gateway</p>
          </div>
        </div>

        {/* Navigation Tabs with Smooth Transitions */}
        <nav className="hidden md:flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('home')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all duration-200 border ${
              activeTab === 'home'
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40'
                : 'text-slate-300 border-transparent hover:text-white'
            }`}
          >
            🏠 Home
          </button>
          <button
            onClick={() => setActiveTab('soc')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all duration-200 border ${
              activeTab === 'soc'
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40'
                : 'text-slate-300 border-transparent hover:text-white'
            }`}
          >
            🛡️ SOC Operations
          </button>
          <button
            onClick={() => setActiveTab('quarantine')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all duration-200 border flex items-center gap-1.5 ${
              activeTab === 'quarantine'
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40'
                : 'text-slate-300 border-transparent hover:text-white'
            }`}
          >
            📦 Quarantine
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-rose-500/20 text-rose-400 border border-rose-500/30">
              {quarantineItems.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-all duration-200 border ${
              activeTab === 'audit'
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40'
                : 'text-slate-300 border-transparent hover:text-white'
            }`}
          >
            📋 Audit Trail
          </button>
        </nav>

        <div className="flex items-center gap-3 text-xs">
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
          >
            OpenAPI Docs
          </a>
          <span className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 font-medium flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            Protected
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 flex-1 w-full transition-all duration-300 ease-in-out">
        {/* TAB 1: HOME SCREEN */}
        {activeTab === 'home' && (
          <div className="space-y-8 animate-fadeIn">
            {/* Hero Banner */}
            <section className="relative rounded-3xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800 p-8 sm:p-12 overflow-hidden shadow-2xl">
              <div className="relative max-w-3xl space-y-5">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                  🛡️ Active Cyber Defense Gateway
                </div>
                <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
                  Stop AI Memory Poisoning Before Context Persists.
                </h1>
                <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
                  NexByte MemoryShield sits as an active security perimeter between autonomous AI agents and long-term memory (LTM) / RAG stores. It inspects memory writes, validates identity provenance, calculates semantic drift, and filters prompt context with zero-trust rigor.
                </p>

                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <button
                    onClick={() => setActiveTab('soc')}
                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition flex items-center gap-2"
                  >
                    Launch SOC Operations Center &rarr;
                  </button>
                  <button
                    onClick={() => setActiveTab('quarantine')}
                    className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
                  >
                    Inspect Quarantine Queue ({quarantineItems.length})
                  </button>
                </div>
              </div>
            </section>

            {/* Quick Metrics */}
            <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 transition hover:-translate-y-1">
                <p className="text-xs text-slate-400">Verified Memories</p>
                <p className="text-2xl font-bold text-white mt-1">{stats ? stats.total_active : '-'}</p>
                <p className="text-[11px] text-emerald-400 mt-1">Clean RAG Index</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 transition hover:-translate-y-1">
                <p className="text-xs text-slate-400">Threats Neutralized</p>
                <p className="text-2xl font-bold text-rose-400 mt-1">{stats ? stats.threats_prevented_count : '-'}</p>
                <p className="text-[11px] text-slate-400 mt-1">Poison writes thwarted</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 transition hover:-translate-y-1">
                <p className="text-xs text-slate-400">Security Latency</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">&lt; 4.8 ms</p>
                <p className="text-[11px] text-slate-400 mt-1">Inline gateway scan</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 transition hover:-translate-y-1">
                <p className="text-xs text-slate-400">Trust Architecture</p>
                <p className="text-2xl font-bold text-purple-400 mt-1">Zero-Trust</p>
                <p className="text-[11px] text-slate-400 mt-1">Perimeter filter active</p>
              </div>
            </section>

            {/* 4-Stage Architecture */}
            <section className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                📐 4-Stage Zero-Trust Defense Pipeline
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="text-cyan-400 font-bold">01 | DETECT</div>
                  <h3 className="font-bold text-white">Heuristic AST Scanning</h3>
                  <p className="text-slate-400 leading-relaxed">
                    Scans memory writes for prompt overrides, jailbreak role changes, and burst injections.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="text-blue-400 font-bold">02 | VERIFY</div>
                  <h3 className="font-bold text-white">Provenance & Drift</h3>
                  <p className="text-slate-400 leading-relaxed">
                    Validates caller claims against session tokens, and scores cosine drift against verified baselines.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="text-amber-400 font-bold">03 | QUARANTINE</div>
                  <h3 className="font-bold text-white">Secure Partitioning</h3>
                  <p className="text-slate-400 leading-relaxed">
                    Isolates high-risk inputs from vector storage, enabling human-in-the-loop analyst triage.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="text-emerald-400 font-bold">04 | PROTECT</div>
                  <h3 className="font-bold text-white">Sanitized Retrieval</h3>
                  <p className="text-slate-400 leading-relaxed">
                    Filters prompt queries so zero adversarial tokens ever reach the AI system prompt.
                  </p>
                </div>
              </div>
            </section>
          </div>
        )}

        {/* TAB 2: SOC OPERATIONS */}
        {activeTab === 'soc' && (
          <div className="space-y-6 animate-fadeIn">
            <TelemetryCards stats={stats} />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-6 space-y-6">
                <IngestSandbox onIngestSuccess={refreshAll} />
              </div>

              <div className="lg:col-span-6 space-y-6">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 mb-2">
                    Safe Context Retrieval (Stage 04: PROTECT)
                  </h3>
                  <p className="text-xs text-slate-400 mb-3">
                    Query the memory store to verify zero-trust perimeter filtering.
                  </p>
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

                <div className="p-5 rounded-2xl bg-gradient-to-br from-rose-950/40 to-slate-900 border border-rose-900/40 flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-white">Quarantine Queue ({quarantineItems.length})</h4>
                    <p className="text-xs text-slate-400 mt-1">Review isolated memory entries awaiting analyst decision.</p>
                  </div>
                  <button
                    onClick={() => setActiveTab('quarantine')}
                    className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-slate-950 font-bold text-xs"
                  >
                    Open Queue &rarr;
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: QUARANTINE */}
        {activeTab === 'quarantine' && (
          <div className="animate-fadeIn">
            <QuarantineTable
              items={quarantineItems}
              onResolve={handleResolveQuarantine}
              onRefresh={fetchQuarantine}
            />
          </div>
        )}

        {/* TAB 4: AUDIT TRAIL */}
        {activeTab === 'audit' && (
          <div className="animate-fadeIn">
            <AuditTrail logs={auditLogs} onRefresh={fetchAudit} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500 bg-slate-950">
        NexByte MemoryShield &bull; Active AI Memory Defense &bull; Production Security Gateway
      </footer>
    </div>
  );
}
