import { useState, useEffect, useCallback } from "react";
import { memoryApi } from "../services/api";

const CATEGORY_COLORS = {
  Names: "bg-blue-500/20 text-blue-400",
  Preferences: "bg-purple-500/20 text-purple-400",
  Location: "bg-green-500/20 text-green-400",
  Projects: "bg-orange-500/20 text-orange-400",
  Goals: "bg-yellow-500/20 text-yellow-400",
  Skills: "bg-cyan-500/20 text-cyan-400",
  Facts: "bg-pink-500/20 text-pink-400",
  General: "bg-neutral-500/20 text-neutral-400",
};

const CATEGORY_ICONS = {
  Names: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  Preferences: "M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z",
  Location: "M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z",
  Projects: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
  Goals: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  Skills: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  Facts: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  General: "M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4",
};

function MemoryPage() {
  const [memories, setMemories] = useState([]);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const loadMemories = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [memRes, statsRes] = await Promise.all([
        memoryApi.list(activeCategory),
        memoryApi.stats(),
      ]);
      setMemories(memRes.data);
      setStats(statsRes.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [activeCategory]);

  useEffect(() => {
    loadMemories();
  }, [loadMemories]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const { data } = await memoryApi.search(searchQuery, activeCategory);
      setSearchResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await memoryApi.delete(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      if (searchResults) {
        setSearchResults((prev) => prev.filter((m) => m.id !== id));
      }
      setDeleteConfirm(null);
      // Refresh stats
      const { data } = await memoryApi.stats();
      setStats(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleClearAll = async () => {
    try {
      await memoryApi.clearAll();
      setMemories([]);
      setSearchResults(null);
      const { data } = await memoryApi.stats();
      setStats(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const displayMemories = searchResults || memories;
  const categories = stats?.categories || {};

  return (
    <div className="min-h-screen bg-chat-bg">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Memory</h1>
          <p className="text-neutral-400 text-sm">
            View and manage what the assistant remembers about you.
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-xs text-neutral-400 mt-1">Total Memories</p>
            </div>
            <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
              <p className="text-2xl font-bold text-white">{Object.keys(categories).length}</p>
              <p className="text-xs text-neutral-400 mt-1">Categories</p>
            </div>
            <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${stats.redis_available ? "bg-green-500" : "bg-red-500"}`} />
                <p className="text-sm text-white">{stats.redis_fallback ? "FakeRedis" : "Redis"}</p>
              </div>
              <p className="text-xs text-neutral-400 mt-1">Short-term Memory</p>
            </div>
            <div className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${stats.chromadb_available ? "bg-green-500" : "bg-red-500"}`} />
                <p className="text-sm text-white">ChromaDB</p>
              </div>
              <p className="text-xs text-neutral-400 mt-1">Long-term Memory</p>
            </div>
          </div>
        )}

        {/* Search Bar */}
        <div className="flex gap-3 mb-6">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search memories..."
              className="w-full px-4 py-2.5 bg-neutral-800 border border-neutral-600 rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-accent transition-colors"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching || !searchQuery.trim()}
            className="px-4 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
          {searchResults && (
            <button
              onClick={() => { setSearchResults(null); setSearchQuery(""); }}
              className="px-4 py-2.5 bg-neutral-700 hover:bg-neutral-600 rounded-xl text-sm text-white transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              !activeCategory
                ? "bg-accent text-white"
                : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
            }`}
          >
            All ({stats?.total || 0})
          </button>
          {Object.entries(categories).map(([cat, count]) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat === activeCategory ? null : cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeCategory === cat
                  ? "bg-accent text-white"
                  : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
              }`}
            >
              {cat} ({count})
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Memories List */}
        {!isLoading && (
          <div className="space-y-3">
            {displayMemories.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-12 h-12 text-neutral-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p className="text-neutral-400 text-sm">
                  {searchResults ? "No memories found for this search." : "No memories stored yet."}
                </p>
                <p className="text-neutral-500 text-xs mt-1">
                  Memories are automatically created when you share personal information.
                </p>
              </div>
            ) : (
              displayMemories.map((memory) => {
                const category = memory.metadata?.category || "general";
                const colorClass = CATEGORY_COLORS[category] || CATEGORY_COLORS.General;
                const iconPath = CATEGORY_ICONS[category] || CATEGORY_ICONS.General;
                const timestamp = memory.metadata?.timestamp
                  ? new Date(memory.metadata.timestamp).toLocaleDateString()
                  : "Unknown";

                return (
                  <div
                    key={memory.id}
                    className="bg-neutral-800 border border-neutral-700/50 rounded-xl p-4 hover:border-neutral-600 transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white leading-relaxed">{memory.content}</p>
                        <div className="flex items-center gap-3 mt-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium ${colorClass}`}>
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={iconPath} />
                            </svg>
                            {category}
                          </span>
                          <span className="text-xs text-neutral-500">{timestamp}</span>
                          {memory.similarity && (
                            <span className="text-xs text-neutral-500">
                              {Math.round(memory.similarity * 100)}% match
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {deleteConfirm === memory.id ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleDelete(memory.id)}
                              className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="px-2 py-1 bg-neutral-600 hover:bg-neutral-500 rounded text-xs text-white"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(memory.id)}
                            className="p-1.5 rounded-lg hover:bg-red-900/50 text-neutral-400 hover:text-red-400 transition-colors"
                            title="Delete memory"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Clear All */}
        {!isLoading && memories.length > 0 && (
          <div className="mt-8 pt-6 border-t border-neutral-700/50">
            <button
              onClick={handleClearAll}
              className="px-4 py-2 bg-red-900/30 hover:bg-red-900/50 border border-red-500/30 rounded-xl text-sm text-red-400 transition-colors"
            >
              Clear All Memories
            </button>
          </div>
        )}

        {/* Model Info */}
        {stats && (
          <div className="mt-6 text-center">
            <p className="text-xs text-neutral-600">
              Embedding model: {stats.embedding_model}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryPage;
