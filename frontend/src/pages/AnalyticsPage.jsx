import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { analyticsApi } from "../services/api";

function BarChart({ data, maxVal, color = "bg-accent" }) {
  if (!data || data.length === 0) return null;
  const max = maxVal || Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="flex items-end gap-1 h-32">
      {data.map((d, i) => (
        <div key={i} className="flex flex-col items-center flex-1 min-w-0 group">
          <div className="text-[10px] text-neutral-500 mb-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {d.value}
          </div>
          <div
            className={`w-full rounded-t ${color} transition-all duration-300 min-h-[2px]`}
            style={{ height: `${Math.max((d.value / max) * 100, 2)}%` }}
          />
          <div className="text-[9px] text-neutral-600 mt-1 truncate w-full text-center">
            {d.label}
          </div>
        </div>
      ))}
    </div>
  );
}

function StatCard({ label, value, sub, icon, color = "text-white" }) {
  return (
    <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
      <div className="flex items-center gap-3 mb-2">
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-neutral-700/50 flex items-center justify-center">
            <svg className="w-4 h-4 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
            </svg>
          </div>
        )}
        <p className="text-xs text-neutral-400">{label}</p>
      </div>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-neutral-500 mt-1">{sub}</p>}
    </div>
  );
}

function AnalyticsPage() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [tools, setTools] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [traces, setTraces] = useState([]);
  const [history, setHistory] = useState([]);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [days]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, tlRes, pfRes, trRes, hsRes] = await Promise.all([
        analyticsApi.overview(days),
        analyticsApi.tools(),
        analyticsApi.performance(),
        analyticsApi.traces(10),
        analyticsApi.history(30),
      ]);
      setOverview(ovRes.data);
      setTools(tlRes.data);
      setPerformance(pfRes.data);
      setTraces(trRes.data);
      setHistory(hsRes.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatMs = (ms) => {
    if (ms > 1000) return `${(ms / 1000).toFixed(1)}s`;
    return `${Math.round(ms)}ms`;
  };

  const dailyData = overview?.daily_breakdown?.map((d) => ({
    label: d.date.slice(5),
    value: d.chats,
  })) || [];

  const dailyLatency = overview?.daily_breakdown?.map((d) => ({
    label: d.date.slice(5),
    value: d.avg_latency,
  })) || [];

  const toolData = tools?.tool_usage
    ? Object.entries(tools.tool_usage).map(([name, count]) => ({
        label: name.replace("_", " "),
        value: count,
      }))
    : [];

  return (
    <div className="min-h-screen bg-chat-bg">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <button
                onClick={() => navigate("/")}
                className="p-2 rounded-lg hover:bg-sidebar-hover text-neutral-400 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
            </div>
            <p className="text-neutral-400 text-sm ml-11">Monitor system performance and usage</p>
          </div>
          <div className="flex items-center gap-2">
            {[7, 14, 30].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  days === d
                    ? "bg-accent text-white"
                    : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
                }`}
              >
                {d}d
              </button>
            ))}
            <button
              onClick={loadData}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-neutral-800 text-neutral-400 hover:bg-neutral-700 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        ) : overview ? (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard
                label="Total Conversations"
                value={overview.db_total_chats || 0}
                sub={`${overview.db_successful || 0} successful`}
                icon="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                color="text-accent"
              />
              <StatCard
                label="Avg Response Time"
                value={formatMs(overview.avg_response_time_ms || 0)}
                sub={`p95: ${formatMs(overview.p95_response_time_ms || 0)}`}
                icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                color="text-blue-400"
              />
              <StatCard
                label="Tool Invocations"
                value={overview.total_tool_invocations || 0}
                sub={`${tools?.tool_usage ? Object.keys(tools.tool_usage).length : 0} tools used`}
                icon="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                color="text-amber-400"
              />
              <StatCard
                label="Success Rate"
                value={
                  overview.db_total_chats > 0
                    ? `${Math.round(((overview.db_successful || 0) / overview.db_total_chats) * 100)}%`
                    : "N/A"
                }
                sub={`${overview.db_failed || 0} failures`}
                icon="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                color="text-green-400"
              />
            </div>

            {/* Second row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard
                label="Memory Hits"
                value={overview.db_total_memory_hits || 0}
                icon="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                color="text-purple-400"
              />
              <StatCard
                label="RAG Hits"
                value={overview.db_total_rag_hits || 0}
                icon="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                color="text-orange-400"
              />
              <StatCard
                label="Failed Requests"
                value={overview.db_failed || 0}
                sub={overview.db_failed > 0 ? "Check error logs" : "No errors"}
                icon="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                color={overview.db_failed > 0 ? "text-red-400" : "text-green-400"}
              />
              <StatCard
                label="Uptime"
                value={overview.uptime_seconds ? `${Math.round(overview.uptime_seconds / 60)}m` : "N/A"}
                sub={`Since ${overview.started_at ? new Date(overview.started_at).toLocaleTimeString() : "N/A"}`}
                icon="M13 10V3L4 14h7v7l9-11h-7z"
                color="text-cyan-400"
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {/* Daily Conversations */}
              <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-5">
                <h3 className="text-sm font-medium text-white mb-4">Daily Conversations</h3>
                <BarChart data={dailyData} color="bg-accent" />
              </div>

              {/* Daily Latency */}
              <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-5">
                <h3 className="text-sm font-medium text-white mb-4">Avg Response Time (ms)</h3>
                <BarChart data={dailyLatency} color="bg-blue-500" />
              </div>

              {/* Tool Usage */}
              <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-5">
                <h3 className="text-sm font-medium text-white mb-4">Tool Usage</h3>
                {toolData.length > 0 ? (
                  <BarChart data={toolData} color="bg-amber-500" />
                ) : (
                  <p className="text-neutral-500 text-sm text-center py-8">No tool calls recorded</p>
                )}
              </div>

              {/* Endpoint Performance */}
              <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-5">
                <h3 className="text-sm font-medium text-white mb-4">Endpoint Latency</h3>
                {performance?.db_endpoints && Object.keys(performance.db_endpoints).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(performance.db_endpoints).map(([ep, data]) => (
                      <div key={ep} className="flex items-center justify-between">
                        <span className="text-xs text-neutral-400 truncate flex-1 mr-3">{ep}</span>
                        <span className="text-xs text-white font-mono">{Math.round(data.avg_latency_ms)}ms</span>
                        <span className="text-[10px] text-neutral-500 ml-2">({data.count})</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-neutral-500 text-sm text-center py-8">No endpoint data</p>
                )}
              </div>
            </div>

            {/* Agent Traces */}
            {traces.length > 0 && (
              <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-5 mb-8">
                <h3 className="text-sm font-medium text-white mb-4">Recent Agent Traces</h3>
                <div className="space-y-3">
                  {traces.map((t) => (
                    <div key={t.id} className="bg-neutral-900 rounded-lg p-3 border border-neutral-700/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] text-neutral-500 font-mono">{t.request_id}</span>
                        <span className="text-[10px] text-neutral-500">{formatMs(t.total_latency_ms)}</span>
                      </div>
                      <div className="flex items-center gap-1 flex-wrap">
                        {t.trace?.map((step, i) => (
                          <span key={i} className="flex items-center gap-1">
                            {i > 0 && <span className="text-neutral-600 text-[10px]">&#8594;</span>}
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                                step.status === "completed"
                                  ? "bg-green-500/20 text-green-400"
                                  : "bg-red-500/20 text-red-400"
                              }`}
                            >
                              {step.agent}
                              {step.latency_ms ? ` ${Math.round(step.latency_ms)}ms` : ""}
                            </span>
                          </span>
                        ))}
                      </div>
                      {t.supervisor_reasoning && (
                        <p className="text-[10px] text-neutral-500 mt-2">{t.supervisor_reasoning}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Request History */}
            {history.length > 0 && (
              <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-5 mb-8">
                <h3 className="text-sm font-medium text-white mb-4">Recent Requests</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-neutral-700/50">
                        <th className="text-left py-2 px-2 text-neutral-400 font-medium">Time</th>
                        <th className="text-left py-2 px-2 text-neutral-400 font-medium">Status</th>
                        <th className="text-left py-2 px-2 text-neutral-400 font-medium">Latency</th>
                        <th className="text-left py-2 px-2 text-neutral-400 font-medium">Route</th>
                        <th className="text-left py-2 px-2 text-neutral-400 font-medium">Tools</th>
                        <th className="text-left py-2 px-2 text-neutral-400 font-medium">Mem</th>
                        <th className="text-left py-2 px-2 text-neutral-400 font-medium">RAG</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((h) => (
                        <tr key={h.id} className="border-b border-neutral-700/20 hover:bg-neutral-700/20">
                          <td className="py-2 px-2 text-neutral-300">
                            {new Date(h.created_at).toLocaleTimeString()}
                          </td>
                          <td className="py-2 px-2">
                            {h.success ? (
                              <span className="text-green-400">&#10003;</span>
                            ) : (
                              <span className="text-red-400">&#10007;</span>
                            )}
                          </td>
                          <td className="py-2 px-2 text-neutral-300 font-mono">
                            {Math.round(h.latency_ms)}ms
                          </td>
                          <td className="py-2 px-2 text-neutral-400">
                            {h.agent_route || "-"}
                          </td>
                          <td className="py-2 px-2 text-neutral-400">
                            {h.tools_used?.length || 0}
                          </td>
                          <td className="py-2 px-2 text-neutral-400">{h.memory_hits}</td>
                          <td className="py-2 px-2 text-neutral-400">{h.rag_hits}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-20">
            <p className="text-neutral-400">No analytics data yet. Start chatting to see metrics.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalyticsPage;
