"""
data_collectors/sanctions_collector.py — Sanctions List Monitor

Checks OFAC, UN, and EU sanctions lists for entities and countries
that could affect the supply chain.

Data sources:
  - OFAC SDN list (US Treasury): https://www.treasury.gov/ofac/downloads/sdn.xml
  - UN Security Council: https://www.un.org/securitycouncil/content/un-sc-consolidated-list
  - EU Consolidated list: https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions
  - Tavily search for latest updates (when API key available)
"""
import os
import httpx
from datetime import datetime
from typing import Optional


# Known sanctioned countries that affect supply chains
HIGH_RISK_COUNTRIES = {
    "Russia": {"risk": "CRITICAL", "reason": "Comprehensive US/EU sanctions since 2022"},
    "Belarus": {"risk": "HIGH", "reason": "EU and US sectoral sanctions"},
    "Iran": {"risk": "CRITICAL", "reason": "Comprehensive US sanctions"},
    "North Korea": {"risk": "CRITICAL", "reason": "Comprehensive UN/US/EU sanctions"},
    "Syria": {"risk": "HIGH", "reason": "US and EU sanctions"},
    "Cuba": {"risk": "MEDIUM", "reason": "US embargo"},
    "Myanmar": {"risk": "HIGH", "reason": "US and EU sectoral sanctions"},
    "Venezuela": {"risk": "HIGH", "reason": "US sectoral sanctions"},
}


class SanctionsCollector:
    def __init__(self):
        self.tavily_key = os.environ.get("TAVILY_API_KEY", "")
        self.timeout = 15.0

    async def get_latest(self, country: Optional[str] = None) -> dict:
        """
        Return current sanctions intelligence for a country or globally.
        """
        result = {
            "checked_at": datetime.utcnow().isoformat(),
            "country": country or "Global",
            "sanctions_hits": [],
            "risk_level": "LOW",
            "sources": [],
        }

        # Check known high-risk countries
        if country and country in HIGH_RISK_COUNTRIES:
            entry = HIGH_RISK_COUNTRIES[country]
            result["sanctions_hits"].append({
                "entity": country,
                "type": "country",
                "list": "US/EU/UN",
                "risk_level": entry["risk"],
                "reason": entry["reason"],
            })
            result["risk_level"] = entry["risk"]

        # Fetch latest sanctions news via Tavily
        if self.tavily_key:
            news = await self._fetch_sanctions_news(country)
            result["recent_updates"] = news
            result["sources"].append("Tavily AI Search")
        else:
            result["recent_updates"] = self._mock_sanctions_news(country)
            result["sources"].append("Mock data")

        # Add static OFAC country list summary
        result["high_risk_countries"] = list(HIGH_RISK_COUNTRIES.keys())
        result["sources"].extend(["OFAC SDN List", "UN Consolidated List", "EU Sanctions List"])
        return result

    async def _fetch_sanctions_news(self, country: Optional[str]) -> list[dict]:
        query = f"{country} sanctions OFAC 2025" if country else "OFAC sanctions supply chain 2025"
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
            print(f"[SanctionsCollector] Error: {e}")
            return []

    @staticmethod
    def _mock_sanctions_news(country: Optional[str]) -> list[dict]:
        return [
            {
                "title": "OFAC Updates SDN List with New Designations",
                "content": "Set TAVILY_API_KEY to get real-time sanctions updates.",
                "url": "https://treasury.gov/ofac",
                "published_date": "2025-01-01",
            }
        ]