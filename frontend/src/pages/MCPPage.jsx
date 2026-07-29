import { useState, useEffect, useCallback } from "react";
import { mcpApi } from "../services/api";

function StatusBadge({ status }) {
  const colors = {
    connected: "bg-green-500/20 text-green-400 border-green-500/30",
    disconnected: "bg-neutral-500/20 text-neutral-400 border-neutral-500/30",
    error: "bg-red-500/20 text-red-400 border-red-500/30",
    not_initialized: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    ok: "bg-green-500/20 text-green-400 border-green-500/30",
    degraded: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  };
  const c = colors[status] || "bg-neutral-500/20 text-neutral-400 border-neutral-500/30";
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${c}`}>
      {status}
    </span>
  );
}

function MCPPage() {
  const [servers, setServers] = useState([]);
  const [tools, setTools] = useState([]);
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMsg, setActionMsg] = useState(null);
  const [expandedServer, setExpandedServer] = useState(null);

  const loadAll = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statusRes, serversRes, toolsRes] = await Promise.all([
        mcpApi.status(),
        mcpApi.servers(),
        mcpApi.tools(),
      ]);
      setStatus(statusRes.data);
      setServers(serversRes.data.servers || []);
      setTools(toolsRes.data.tools || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleConnect = async (name) => {
    setActionMsg(`Connecting to ${name}...`);
    try {
      await mcpApi.connect(name);
      setActionMsg(`Connected to ${name}`);
      loadAll();
    } catch (err) {
      setActionMsg(`Failed: ${err.message}`);
    }
    setTimeout(() => setActionMsg(null), 3000);
  };

  const handleDisconnect = async (name) => {
    setActionMsg(`Disconnecting from ${name}...`);
    try {
      await mcpApi.disconnect(name);
      setActionMsg(`Disconnected from ${name}`);
      loadAll();
    } catch (err) {
      setActionMsg(`Failed: ${err.message}`);
    }
    setTimeout(() => setActionMsg(null), 3000);
  };

  const handleRefresh = async () => {
    setActionMsg("Refreshing...");
    try {
      await mcpApi.refresh();
      setActionMsg("Refreshed");
      loadAll();
    } catch (err) {
      setActionMsg(`Refresh failed: ${err.message}`);
    }
    setTimeout(() => setActionMsg(null), 3000);
  };

  const getServerTools = (serverName) =>
    tools.filter((t) => t.server === serverName);

  return (
    <div className="min-h-screen bg-[#212121] text-white p-4 lg:ml-64">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">MCP Servers</h1>
            <p className="text-sm text-neutral-400 mt-1">
              Model Context Protocol — connect to external tools and services
            </p>
          </div>
          <div className="flex items-center gap-3">
            {actionMsg && (
              <span className="text-sm text-accent animate-pulse">{actionMsg}</span>
            )}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent/90 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              <svg className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {status && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Status</p>
              <div className="mt-2"><StatusBadge status={status.status} /></div>
            </div>
            <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Connected</p>
              <p className="text-2xl font-bold mt-1">{status.connected || 0}/{status.total || 0}</p>
            </div>
            <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Servers</p>
              <p className="text-2xl font-bold mt-1">{status.total_servers || 0}</p>
            </div>
            <div className="bg-neutral-800/50 rounded-xl p-4 border border-neutral-700/50">
              <p className="text-xs text-neutral-500 uppercase tracking-wider">Total Tools</p>
              <p className="text-2xl font-bold mt-1">{status.total_tools || 0}</p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!isLoading && (
          <>
            {/* Servers List */}
            <div className="space-y-4 mb-8">
              <h2 className="text-lg font-semibold text-neutral-200">Servers</h2>
              {servers.length === 0 ? (
                <div className="bg-neutral-800/50 rounded-xl p-8 text-center border border-neutral-700/50">
                  <svg className="w-12 h-12 mx-auto text-neutral-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                  </svg>
                  <p className="text-neutral-400">No MCP servers configured</p>
                  <p className="text-xs text-neutral-500 mt-1">
                    Add MCP_SERVERS to your .env file
                  </p>
                </div>
              ) : (
                servers.map((server) => {
                  const svrTools = getServerTools(server.name);
                  const isExpanded = expandedServer === server.name;
                  return (
                    <div key={server.name} className="bg-neutral-800/50 rounded-xl border border-neutral-700/50 overflow-hidden">
                      <div className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                            </svg>
                          </div>
                          <div>
                            <h3 className="font-medium">{server.name}</h3>
                            <p className="text-xs text-neutral-500">
                              {server.command} {server.args?.join(" ")}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <StatusBadge status={server.status} />
                          {svrTools.length > 0 && (
                            <span className="text-xs text-neutral-400">{svrTools.length} tools</span>
                          )}
                          <button
                            onClick={() => setExpandedServer(isExpanded ? null : server.name)}
                            className="p-1 rounded hover:bg-neutral-700 text-neutral-400"
                          >
                            <svg className={`w-4 h-4 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                          {server.status === "disconnected" ? (
                            <button
                              onClick={() => handleConnect(server.name)}
                              className="px-3 py-1.5 bg-accent hover:bg-accent/90 text-white rounded-lg text-xs transition-colors"
                            >
                              Connect
                            </button>
                          ) : (
                            <button
                              onClick={() => handleDisconnect(server.name)}
                              className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-xs transition-colors"
                            >
                              Disconnect
                            </button>
                          )}
                        </div>
                      </div>
                      {isExpanded && svrTools.length > 0 && (
                        <div className="border-t border-neutral-700/50 px-4 py-3 space-y-2">
                          <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Available Tools</p>
                          {svrTools.map((tool) => (
                            <div key={tool.name} className="bg-neutral-700/30 rounded-lg p-3">
                              <div className="flex items-start justify-between">
                                <div>
                                  <p className="text-sm font-medium text-accent">{tool.name}</p>
                                  {tool.description && (
                                    <p className="text-xs text-neutral-400 mt-0.5">{tool.description}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      {isExpanded && svrTools.length === 0 && (
                        <div className="border-t border-neutral-700/50 px-4 py-3">
                          <p className="text-xs text-neutral-500">No tools available</p>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {/* All Tools */}
            <div>
              <h2 className="text-lg font-semibold text-neutral-200 mb-4">
                All Tools ({tools.length})
              </h2>
              {tools.length === 0 ? (
                <div className="bg-neutral-800/50 rounded-xl p-8 text-center border border-neutral-700/50">
                  <p className="text-neutral-400">No tools discovered</p>
                  <p className="text-xs text-neutral-500 mt-1">
                    Connect to an MCP server to see its tools
                  </p>
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {tools.map((tool) => (
                    <div key={`${tool.server}-${tool.name}`} className="bg-neutral-800/50 rounded-lg p-4 border border-neutral-700/50 hover:border-accent/30 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <p className="text-sm font-medium text-accent truncate">{tool.name}</p>
                        <span className="text-xs text-neutral-500 shrink-0 ml-2">{tool.server}</span>
                      </div>
                      {tool.description && (
                        <p className="text-xs text-neutral-400 line-clamp-2">{tool.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default MCPPage;
