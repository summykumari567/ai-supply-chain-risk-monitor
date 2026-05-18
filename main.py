"""
AI Supply Chain Risk Monitor — FastAPI Backend
Monitors news, sanctions, weather, and geopolitical events to predict
supply chain disruptions and recommend alternative suppliers.
"""
import os
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from agent import RiskMonitorAgent
from neo4j_client import Neo4jClient
from kafka_producer import RiskEventProducer

app = FastAPI(
    title="AI Supply Chain Risk Monitor",
    description="Real-time supply chain risk monitoring with AI-powered disruption prediction.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = RiskMonitorAgent()
neo4j = Neo4jClient()
producer = RiskEventProducer()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()


# ── Request Models ─────────────────────────────────────────────────────────────

class SupplierInput(BaseModel):
    name: str
    country: str
    category: str
    tier: int = 1
    annual_spend_usd: Optional[float] = None
    products: Optional[list[str]] = None

class RiskQueryInput(BaseModel):
    supplier_name: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    include_alternatives: bool = True

class DisruptionAlertInput(BaseModel):
    event_type: str
    description: str
    affected_regions: list[str]
    severity: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/suppliers")
async def add_supplier(supplier: SupplierInput):
    result = neo4j.create_supplier(supplier.dict())
    return {"status": "created", "supplier": result}


@app.get("/suppliers")
async def list_suppliers():
    return neo4j.get_all_suppliers()


@app.get("/suppliers/{supplier_name}/risk")
async def get_supplier_risk(supplier_name: str, include_alternatives: bool = True):
    try:
        result = await agent.assess_supplier_risk(supplier_name, include_alternatives)
        await producer.publish_risk_event(supplier_name, result)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/analyze")
async def analyze_risk(query: RiskQueryInput):
    try:
        result = await agent.run_full_analysis(
            supplier_name=query.supplier_name,
            country=query.country,
            category=query.category,
            include_alternatives=query.include_alternatives,
        )
        await manager.broadcast({"type": "risk_update", "data": result})
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/dashboard")
async def get_dashboard():
    try:
        return await agent.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/sanctions")
async def get_sanctions_feed():
    from data_collectors.sanctions_collector import SanctionsCollector
    return await SanctionsCollector().get_latest()


@app.get("/weather-risks")
async def get_weather_risks():
    from data_collectors.weather_collector import WeatherCollector
    return await WeatherCollector().get_risk_events()


@app.get("/geopolitical")
async def get_geopolitical_events():
    from data_collectors.geo_collector import GeopoliticalCollector
    return await GeopoliticalCollector().get_events()


@app.get("/graph")
async def get_supply_chain_graph():
    return neo4j.get_graph_data()


@app.post("/alerts")
async def create_alert(alert: DisruptionAlertInput):
    event = {
        "type": "disruption_alert",
        "event_type": alert.event_type,
        "description": alert.description,
        "affected_regions": alert.affected_regions,
        "severity": alert.severity,
    }
    await producer.publish_alert(event)
    await manager.broadcast(event)
    return {"status": "alert_published", "event": event}


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_json({"type": "ping", "status": "ok"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)