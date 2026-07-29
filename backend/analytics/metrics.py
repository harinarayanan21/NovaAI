import time
import threading
from collections import defaultdict
from datetime import datetime, timezone


class MetricsCollector:
    """Thread-safe in-memory metrics collector for real-time counters."""

    def __init__(self):
        self._lock = threading.RLock()
        self._counters = defaultdict(int)
        self._timers = defaultdict(list)
        self._start_time = time.time()

    def increment(self, key: str, amount: int = 1):
        with self._lock:
            self._counters[key] += amount

    def record_latency(self, key: str, latency_ms: float):
        with self._lock:
            self._timers[key].append(latency_ms)
            if len(self._timers[key]) > 10000:
                self._timers[key] = self._timers[key][-5000:]

    def get_counter(self, key: str) -> int:
        with self._lock:
            return self._counters.get(key, 0)

    def get_avg_latency(self, key: str) -> float:
        with self._lock:
            vals = self._timers.get(key, [])
            if not vals:
                return 0.0
            return sum(vals) / len(vals)

    def get_p95_latency(self, key: str) -> float:
        with self._lock:
            vals = self._timers.get(key, [])
            if not vals:
                return 0.0
            sorted_vals = sorted(vals)
            idx = int(len(sorted_vals) * 0.95)
            return sorted_vals[min(idx, len(sorted_vals) - 1)]

    def get_overview(self) -> dict:
        with self._lock:
            uptime = time.time() - self._start_time
            return {
                "total_requests": self._counters.get("total_requests", 0),
                "successful_requests": self._counters.get("successful_requests", 0),
                "failed_requests": self._counters.get("failed_requests", 0),
                "total_chat_messages": self._counters.get("chat_messages", 0),
                "total_tool_invocations": self._counters.get("tool_invocations", 0),
                "total_rag_queries": self._counters.get("rag_queries", 0),
                "total_memory_retrievals": self._counters.get("memory_retrievals", 0),
                "total_mcp_requests": self._counters.get("mcp_requests", 0),
                "total_vision_requests": self._counters.get("vision_requests", 0),
                "total_ocr_requests": self._counters.get("ocr_requests", 0),
                "total_vision_uploads": self._counters.get("vision_uploads", 0),
                "total_tokens_used": self._counters.get("tokens_used", 0),
                "avg_response_time_ms": round(self.get_avg_latency("chat_latency"), 2),
                "p95_response_time_ms": round(self.get_p95_latency("chat_latency"), 2),
                "uptime_seconds": round(uptime, 1),
                "started_at": datetime.fromtimestamp(
                    self._start_time, tz=timezone.utc
                ).isoformat(),
            }

    def get_tool_stats(self) -> dict:
        with self._lock:
            tool_counts = {}
            for key, val in self._counters.items():
                if key.startswith("tool_"):
                    tool_name = key.replace("tool_", "")
                    tool_counts[tool_name] = val
            return {
                "tool_usage": tool_counts,
                "total_tool_calls": self._counters.get("tool_invocations", 0),
            }

    def get_performance_stats(self) -> dict:
        with self._lock:
            endpoints = {}
            for key, vals in self._timers.items():
                if key.startswith("latency_"):
                    endpoint = key.replace("latency_", "")
                    if vals:
                        endpoints[endpoint] = {
                            "avg_ms": round(sum(vals) / len(vals), 2),
                            "p95_ms": round(
                                sorted(vals)[int(len(vals) * 0.95)]
                                if len(vals) > 1
                                else vals[0],
                                2,
                            ),
                            "count": len(vals),
                        }
            return {
                "endpoints": endpoints,
                "avg_chat_latency": round(self.get_avg_latency("chat_latency"), 2),
                "p95_chat_latency": round(self.get_p95_latency("chat_latency"), 2),
            }


metrics = MetricsCollector()
