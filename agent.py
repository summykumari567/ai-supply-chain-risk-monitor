"""
agent.py — Claude-Powered Supply Chain Risk Monitor Agent

Pipeline per analysis:
  1. Collect: news + sanctions + weather + geopolitical (parallel)
  2. Claude: synthesize all signals, score risk, predict disruptions
  3. Claude: recommend alternative suppliers with impact assessments
  4. Return structured risk report
"""
import asyncio
import json
from datetime import datetime
from typing import Optional

import anthropic

from data_collectors.news_collector import NewsCollector
from data_collectors.sanctions_collector import SanctionsCollector
from data_collectors.weather_collector import WeatherCollector
from data_collectors.geo_collector import GeopoliticalCollector


RISK_ANALYSIS_PROMPT = """You are a senior supply chain risk analyst. Analyze all provided intelligence data and produce a comprehensive risk assessment.

Return ONLY valid JSON (no markdown, no preamble) matching this schema:
{{
  "overall_risk_score": <0-100>,
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "confidence": <0.0-1.0>,
  "disruption_probability_30d": <0.0-1.0>,
  "disruption_probability_90d": <0.0-1.0>,
  "executive_summary": "<2-3 paragraph summary for supply chain managers>",
  "risk_factors": [
    {{
      "category": "<sanctions|weather|geopolitical|news|logistics>",
      "title": "...",
      "description": "...",
      "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "affected_regions": ["..."],
      "estimated_impact_days": <int>,
      "probability": <0.0-1.0>
    }}
  ],
  "alternative_suppliers": [
    {{
      "name": "...",
      "country": "...",
      "risk_score": <0-100>,
      "capacity_match": "<FULL|PARTIAL|LIMITED>",
      "lead_time_days": <int>,
      "estimated_transition_cost_usd": <int or null>,
      "rationale": "..."
    }}
  ],
  "recommendations": [
    {{
      "priority": "<IMMEDIATE|SHORT_TERM|LONG_TERM>",
      "action": "...",
      "expected_outcome": "...",
      "estimated_cost_usd": <int or null>
    }}
  ],
  "monitoring_triggers": ["<event that should trigger re-analysis>"],
  "next_review_date": "<YYYY-MM-DD>"
}}

Analysis scope:
- Supplier: {supplier_name}
- Country: {country}
- Category: {category}
- Analysis date: {date}

--- INTELLIGENCE DATA ---

NEWS INTELLIGENCE:
{news_data}

SANCTIONS DATA:
{sanctions_data}

WEATHER & LOGISTICS RISKS:
{weather_data}

GEOPOLITICAL EVENTS:
{geo_data}
"""

DASHBOARD_PROMPT = """You are a supply chain risk dashboard AI. Based on the current global risk intelligence, produce a dashboard summary.

Return ONLY valid JSON (no markdown):
{{
  "global_risk_index": <0-100>,
  "risk_trend": "<IMPROVING|STABLE|DETERIORATING>",
  "active_disruptions": <int>,
  "suppliers_at_risk": <int>,
  "top_threats": [
    {{"rank": 1, "threat": "...", "region": "...", "severity": "<LOW|MEDIUM|HIGH|CRITICAL>", "impact": "..."}}
  ],
  "risk_by_region": [
    {{"region": "...", "risk_score": <0-100>, "primary_risk": "..."}}
  ],
  "risk_by_category": [
    {{"category": "...", "risk_score": <0-100>, "trend": "<UP|STABLE|DOWN>"}}
  ],
  "recent_alerts": [
    {{"time": "...", "title": "...", "severity": "...", "affected": "..."}}
  ],
  "summary": "..."
}}

Current date: {date}

NEWS INTELLIGENCE:
{news_data}

SANCTIONS DATA:
{sanctions_data}

WEATHER DATA:
{weather_data}

GEOPOLITICAL DATA:
{geo_data}
"""


class RiskMonitorAgent:
    def __init__(self):
        self.claude = anthropic.Anthropic()
        self.news = NewsCollector()
        self.sanctions = SanctionsCollector()
        self.weather = WeatherCollector()
        self.geo = GeopoliticalCollector()

    async def run_full_analysis(
        self,
        supplier_name: Optional[str] = None,
        country: Optional[str] = None,
        category: Optional[str] = None,
        include_alternatives: bool = True,
    ) -> dict:
        # Step 1: Collect all intelligence in parallel
        news_data, sanctions_data, weather_data, geo_data = await asyncio.gather(
            self.news.collect(supplier_name, country, category),
            self.sanctions.get_latest(country),
            self.weather.get_risk_events(country),
            self.geo.get_events(country),
            return_exceptions=True,
        )

        # Step 2: Claude synthesis
        prompt = RISK_ANALYSIS_PROMPT.format(
            supplier_name=supplier_name or "All Suppliers",
            country=country or "Global",
            category=category or "All Categories",
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            news_data=self._safe_json(news_data),
            sanctions_data=self._safe_json(sanctions_data),
            weather_data=self._safe_json(weather_data),
            geo_data=self._safe_json(geo_data),
        )

        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.claude.messages.create(
                model="claude-opus-4-5",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            ),
        )

        result = json.loads(message.content[0].text.strip())
        result["supplier_name"] = supplier_name
        result["country"] = country
        result["category"] = category
        result["analyzed_at"] = datetime.utcnow().isoformat()
        return result

    async def assess_supplier_risk(
        self, supplier_name: str, include_alternatives: bool = True
    ) -> dict:
        return await self.run_full_analysis(
            supplier_name=supplier_name,
            include_alternatives=include_alternatives,
        )

    async def get_dashboard_summary(self) -> dict:
        news_data, sanctions_data, weather_data, geo_data = await asyncio.gather(
            self.news.collect(),
            self.sanctions.get_latest(),
            self.weather.get_risk_events(),
            self.geo.get_events(),
            return_exceptions=True,
        )

        prompt = DASHBOARD_PROMPT.format(
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            news_data=self._safe_json(news_data),
            sanctions_data=self._safe_json(sanctions_data),
            weather_data=self._safe_json(weather_data),
            geo_data=self._safe_json(geo_data),
        )

        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.claude.messages.create(
                model="claude-opus-4-5",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            ),
        )

        result = json.loads(message.content[0].text.strip())
        result["generated_at"] = datetime.utcnow().isoformat()
        return result

    @staticmethod
    def _safe_json(data) -> str:
        if isinstance(data, Exception):
            return f"Data unavailable: {data}"
        try:
            return json.dumps(data, indent=2)
        except Exception:
            return str(data)