"""
data_collectors/weather_collector.py — Weather & Climate Risk Collector

Fetches weather events that could disrupt supply chain logistics:
  - Hurricanes / typhoons near ports
  - Severe winter storms affecting transportation
  - Flooding near manufacturing hubs
  - Extreme heat affecting factory output
  - Drought affecting raw material supply

Data sources:
  - OpenWeatherMap API (severe alerts)
  - NOAA / NWS weather alerts
  - Tavily news for weather-related logistics disruptions
"""
import os
import httpx
from datetime import datetime
from typing import Optional


# Critical logistics nodes to monitor
CRITICAL_LOGISTICS_NODES = [
    {"name": "Port of Shanghai", "lat": 31.23, "lon": 121.47, "country": "China"},
    {"name": "Port of Rotterdam", "lat": 51.90, "lon": 4.48, "country": "Netherlands"},
    {"name": "Port of Singapore", "lat": 1.26, "lon": 103.82, "country": "Singapore"},
    {"name": "Port of Los Angeles", "lat": 33.73, "lon": -118.26, "country": "USA"},
    {"name": "Suez Canal", "lat": 30.69, "lon": 32.34, "country": "Egypt"},
    {"name": "Panama Canal", "lat": 9.08, "lon": -79.68, "country": "Panama"},
    {"name": "Strait of Malacca", "lat": 2.5, "lon": 101.5, "country": "Malaysia"},
    {"name": "Taiwan Strait", "lat": 23.5, "lon": 119.5, "country": "Taiwan"},
]


class WeatherCollector:
    def __init__(self):
        self.owm_key = os.environ.get("OPENWEATHER_API_KEY", "")
        self.tavily_key = os.environ.get("TAVILY_API_KEY", "")
        self.timeout = 15.0

    async def get_risk_events(self, country: Optional[str] = None) -> dict:
        """
        Return weather risk events affecting supply chain logistics.
        """
        result = {
            "checked_at": datetime.utcnow().isoformat(),
            "monitored_nodes": CRITICAL_LOGISTICS_NODES,
            "active_weather_risks": [],
            "logistics_disruptions": [],
            "sources": [],
        }

        # Fetch weather alerts via OpenWeatherMap
        if self.owm_key:
            alerts = await self._fetch_owm_alerts()
            result["active_weather_risks"] = alerts
            result["sources"].append("OpenWeatherMap API")
        else:
            result["active_weather_risks"] = self._mock_weather_events()
            result["note"] = "Set OPENWEATHER_API_KEY for real weather data"

        # Fetch weather-related logistics news via Tavily
        if self.tavily_key:
            news = await self._fetch_weather_news(country)
            result["logistics_disruptions"] = news
            result["sources"].append("Tavily AI Search")

        return result

    async def _fetch_owm_alerts(self) -> list[dict]:
        """Fetch severe weather alerts near critical logistics nodes."""
        alerts = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for node in CRITICAL_LOGISTICS_NODES[:4]:  # Limit API calls
                try:
                    resp = await client.get(
                        "https://api.openweathermap.org/data/3.0/onecall",
                        params={
                            "lat": node["lat"],
                            "lon": node["lon"],
                            "appid": self.owm_key,
                            "exclude": "minutely,hourly,daily",
                            "units": "metric",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    for alert in data.get("alerts", []):
                        alerts.append({
                            "location": node["name"],
                            "country": node["country"],
                            "event": alert.get("event", ""),
                            "description": alert.get("description", "")[:200],
                            "start": datetime.utcfromtimestamp(alert.get("start", 0)).isoformat(),
                            "end": datetime.utcfromtimestamp(alert.get("end", 0)).isoformat(),
                            "severity": self._classify_severity(alert.get("event", "")),
                        })
                except Exception as e:
                    print(f"[WeatherCollector] Error for {node['name']}: {e}")
        return alerts

    async def _fetch_weather_news(self, country: Optional[str]) -> list[dict]:
        query = (
            f"{country} weather logistics shipping disruption 2025"
            if country
            else "port weather storm shipping disruption logistics 2025"
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
            print(f"[WeatherCollector] News error: {e}")
            return []

    @staticmethod
    def _classify_severity(event: str) -> str:
        event_lower = event.lower()
        if any(w in event_lower for w in ["hurricane", "typhoon", "tornado", "cyclone"]):
            return "CRITICAL"
        if any(w in event_lower for w in ["storm", "flood", "blizzard", "ice"]):
            return "HIGH"
        if any(w in event_lower for w in ["wind", "rain", "snow", "fog"]):
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _mock_weather_events() -> list[dict]:
        return [
            {
                "location": "Taiwan Strait",
                "country": "Taiwan",
                "event": "Typhoon Warning",
                "description": "Mock: Set OPENWEATHER_API_KEY for real weather alerts.",
                "severity": "HIGH",
            },
            {
                "location": "Port of Rotterdam",
                "country": "Netherlands",
                "event": "High Wind Advisory",
                "description": "Mock: Strong winds may delay port operations.",
                "severity": "MEDIUM",
            },
        ]