import json
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo. Returns search results with title, snippet, and URL.

    Args:
        query: Search query string, e.g. "latest news about AI 2025".
        max_results: Maximum number of results to return. Default 5. Max 10.

    Returns:
        JSON with list of search results. Each result has title, snippet, and url.
    """
    try:
        from ddgs import DDGS

        max_results = max(1, min(10, max_results))

        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                })

            if not results:
                return json.dumps({
                    "success": True,
                    "results": [],
                    "message": "No results found. Try a different search query.",
                })

            logger.info("Search for '%s': %d results", query, len(results))
            return json.dumps({"success": True, "results": results})

    except ImportError:
        return json.dumps({"success": False, "error": "duckduckgo-search package not installed"})
    except Exception as e:
        logger.error("Search error: %s", str(e))
        return json.dumps({"success": False, "error": str(e)})
