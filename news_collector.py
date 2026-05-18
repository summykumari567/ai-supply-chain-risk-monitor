"""
data_collectors/news_collector.py — Tavily-powered news intelligence collector

Fetches real-time supply chain news, including:
  - Supplier-specific news
  - Industry/category disruptions
  - Regional trade and logistics updates
"""
import os
from typing import Optional
import httpx


class NewsCollector:
    def __init__(self):
        self.api_key = os.environ.get("TAVILY_API_KEY", "")
        self.base_url = "https://api.tavily.com"
        self.timeout = 20.0

    async def collect(
        self,
        supplier_name: Optional[str] = None,
        country: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        queries = self._build_queries(supplier_name, country, category)
        results = []

        import asyncio
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [self._search(client, q) for q in queries]
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in all_results:
                if isinstance(r, list):
                    results.extend(r)

        # Deduplicate by URL
        seen = set()
        unique = []
        for item in results:
            url = item.get("url", "")
            if url not in seen:
                seen.add(url)
                unique.append(item)

        return unique[:30]

    async def _search(self, client: httpx.AsyncClient, query: str) -> list[dict]:
        if not self.api_key:
            return self._mock_results(query)

        try:
            response = await client.post(
                f"{self.base_url}/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": 6,
                    "search_depth": "advanced",
                    "topic": "news",
                },
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            print(f"[NewsCollector] Error for '{query}': {e}")
            return []

    def _build_queries(
        self,
        supplier_name: Optional[str],
        country: Optional[str],
        category: Optional[str],
    ) -> list[str]:
        queries = []
        if supplier_name:
            queries.append(f"{supplier_name} supply chain disruption 2025")
            queries.append(f"{supplier_name} production delay shortage")
        if country:
            queries.append(f"{country} supply chain trade disruption 2025")
            queries.append(f"{country} manufacturing export restrictions")
        if category:
            queries.append(f"{category} supply chain shortage crisis 2025")
        if not queries:
            queries = [
                "global supply chain disruption 2025",
                "semiconductor shortage logistics crisis",
                "trade war tariffs manufacturing impact",
                "port congestion shipping delays 2025",
            ]
        return queries

    @staticmethod
    def _mock_results(query: str) -> list[dict]:
        return [
            {
                "title": f"[Mock] Supply chain news for: {query}",
                "url": "https://example.com",
                "content": "Set TAVILY_API_KEY in .env to enable real news collection.",
                "published_date": "2025-01-01",
                "score": 0.0,
            }
        ]