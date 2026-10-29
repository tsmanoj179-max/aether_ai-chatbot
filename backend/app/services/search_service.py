import re
import urllib.parse
from typing import List, Dict, Any, Optional
import httpx
from backend.app.config import settings

class SearchService:
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes web search via configured provider (Tavily, Brave, or DuckDuckGo API/HTML).
        Returns list of dicts: {'title': ..., 'url': ..., 'snippet': ...}
        """
        query = query.strip()
        if not query:
            return []

        # 1. Try Tavily if configured
        if settings.TAVILY_API_KEY:
            try:
                results = await self._search_tavily(query, max_results)
                if results:
                    return results
            except Exception:
                pass

        # 2. Try Brave if configured
        if settings.BRAVE_API_KEY:
            try:
                results = await self._search_brave(query, max_results)
                if results:
                    return results
            except Exception:
                pass

        # 3. Fallback to DuckDuckGo instant API / HTML
        try:
            return await self._search_duckduckgo(query, max_results)
        except Exception:
            return []

    async def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post("https://api.tavily.com/search", json=payload)
            res.raise_for_status()
            data = res.json()
            return [
                {
                    "title": r.get("title", "Web Result"),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")
                }
                for r in data.get("results", [])
            ]

    async def _search_brave(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": settings.BRAVE_API_KEY
        }
        params = {"q": query, "count": max_results}
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)
            res.raise_for_status()
            data = res.json()
            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", "")
                })
            return results

    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                return []

            html = res.text
            # Lightweight extraction of result snippets from DuckDuckGo HTML
            results = []
            matches = re.findall(
                r'<a[^>]+class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                html,
                re.DOTALL
            )
            
            if not matches:
                # Alternative match pattern
                matches = re.findall(
                    r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^>]*>(.*?)</a>',
                    html,
                    re.DOTALL
                )

            for raw_url, raw_snippet in matches[:max_results]:
                clean_snippet = re.sub(r'<[^>]+>', '', raw_snippet).strip()
                # DuckDuckGo redirect link unquote
                actual_url = raw_url
                if "uddg=" in raw_url:
                    m = re.search(r'uddg=([^&]+)', raw_url)
                    if m:
                        actual_url = urllib.parse.unquote(m.group(1))

                results.append({
                    "title": f"Web Result for '{query}'",
                    "url": actual_url,
                    "snippet": clean_snippet or "Snippet not available."
                })

            return results

search_service = SearchService()
