"""
data_collectors/geo_collector.py — Geopolitical Risk Collector

Monitors geopolitical events that affect supply chains:
  - Trade wars and tariffs
  - Export restrictions and bans
  - Political instability near manufacturing hubs
  - Military conflicts near logistics routes
  - Diplomatic relations changes

Data source: Tavily AI Search (real-time news)
"""
import os
import httpx
from datetime import datetime
from typing import Optional


# High-risk geopolitical flashpoints for supply chains
GEOPOLITICAL_HOTSPOTS = [
    {"region": "Taiwan Strait", "risk": "HIGH", "impact": "Semiconductor supply chain"},
    {"region": "South China Sea", "risk": "HIGH", "impact": "Global shipping routes"},
    {"region": "Middle East", "risk": "HIGH", "impact": "Oil, energy, Suez Canal"},
    {"region": "Eastern Europe", "risk": "HIGH", "impact": "Raw materials, grain, metals"},
    {"region": "Korean Peninsula", "risk": "MEDIUM", "impact": "Electronics manufacturing"},
    {"region": "Strait of Hormuz", "risk": "MEDIUM", "impact": "Energy supply routes"},
]

QUERY_TEMPLATES = [
    "{country} trade war tariff supply chain 2025",
    "{country} export restriction ban technology 2025",
    "{country} political instability manufacturing 2025",
    "geopolitical risk supply chain {category} 2025",
    "US China trade war semiconductor restriction 2025",
    "global trade disruption tariffs 2025",
]


class GeopoliticalCollector:
    def __init__(self):
        self.tavily_key = os.environ.get("TAVILY_API_KEY", "")
        self.timeout = 20.0

    async def get_events(self, country: Optional[str] = None, category: Optional[str] = None) -> dict:
        """Return current geopolitical risk events."""
        result = {
            "checked_at": datetime.utcnow().isoformat(),
            "hotspots": GEOPOLITICAL_HOTSPOTS,
            "active_events": [],
            "trade_restrictions": [],
            "sources": [],
        }

        if self.tavily_key:
            events = await self._fetch_geo_news(country, category)
            trade = await self._fetch_trade_restrictions(country)
            result["active_events"] = events
            result["trade_restrictions"] = trade
            result["sources"].append("Tavily AI Search")
        else:
            result["active_events"] = self._mock_events()
            result["trade_restrictions"] = self._mock_trade_restrictions()
            result["note"] = "Set TAVILY_API_KEY for real geopolitical intelligence"

        return result

    async def _fetch_geo_news(
        self, country: Optional[str], category: Optional[str]
    ) -> list[dict]:
        queries = []
        if country:
            queries.append(f"{country} political risk supply chain 2025")
            queries.append(f"{country} export controls sanctions trade 2025")
        if category:
            queries.append(f"{category} supply chain geopolitical risk 2025")
        if not queries:
            queries = [
                "geopolitical supply chain disruption 2025",
                "US China trade war technology ban 2025",
                "Taiwan semiconductor conflict risk 2025",
            ]

        all_results = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for query in queries[:3]:
                try:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": self.tavily_key,
                            "query": query,
                            "max_results": 5,
                            "topic": "news",
                            "search_depth": "advanced",
                        },
                    )
                    resp.raise_for_status()
                    all_results.extend(resp.json().get("results", []))
                except Exception as e:
                    print(f"[GeoCollector] Error: {e}")

        return all_results

    async def _fetch_trade_restrictions(self, country: Optional[str]) -> list[dict]:
        query = (
            f"{country} export import restriction ban 2025"
            if country
            else "US export controls CHIPS act technology restriction 2025"
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_key,
                        "query": query,
                        "max_results": 5,
                        "topic": "news",
                    },
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[GeoCollector] Trade restriction error: {e}")
            return []

    @staticmethod
    def _mock_events() -> list[dict]:
        return [
            {
                "title": "US-China Semiconductor Export Controls Extended",
                "content": "Mock: Set TAVILY_API_KEY for real geopolitical data.",
                "url": "https://example.com",
                "published_date": "2025-01-01",
                "severity": "HIGH",
            },
            {
                "title": "Taiwan Strait Tensions — Shipping Rerouting",
                "content": "Mock: Shipping companies rerouting cargo as precaution.",
                "url": "https://example.com",
                "published_date": "2025-01-01",
                "severity": "HIGH",
            },
        ]

    @staticmethod
    def _mock_trade_restrictions() -> list[dict]:
        return [
            {
                "title": "CHIPS Act: Advanced Semiconductor Export Restrictions",
                "description": "Mock: US restricts export of advanced chips to certain countries.",
                "affected_countries": ["China"],
                "category": "semiconductors",
                "effective_date": "2024-10-07",
            }
        ]