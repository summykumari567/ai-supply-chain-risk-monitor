"""
kafka_producer.py — Kafka Risk Event Producer

Publishes supply chain risk events to Kafka topics for downstream
consumers (alerting systems, dashboards, ML pipelines).

Topics:
  supply-chain-risk-events    General risk assessments
  supply-chain-alerts         High-severity disruption alerts
  supplier-risk-scores        Per-supplier risk score updates
"""
import os
import json
from datetime import datetime
from typing import Optional

try:
    from confluent_kafka import Producer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


TOPICS = {
    "risk_events": "supply-chain-risk-events",
    "alerts": "supply-chain-alerts",
    "risk_scores": "supplier-risk-scores",
}


class RiskEventProducer:
    def __init__(self):
        self.bootstrap_servers = os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self._producer = None
        self._connect()

    def _connect(self):
        if not KAFKA_AVAILABLE:
            print("[Kafka] confluent-kafka not installed — running in mock mode")
            return
        try:
            self._producer = Producer({
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "supply-chain-risk-monitor",
                "acks": "all",
                "retries": 3,
                "enable.idempotence": True,
            })
            print(f"[Kafka] Producer connected to {self.bootstrap_servers}")
        except Exception as e:
            print(f"[Kafka] Connection failed (mock mode): {e}")
            self._producer = None

    def is_connected(self) -> bool:
        return self._producer is not None

    # ── Publish methods ────────────────────────────────────────────────────────

    async def publish_risk_event(self, supplier_name: str, risk_data: dict):
        """Publish a full risk assessment to the risk-events topic."""
        event = {
            "event_type": "risk_assessment",
            "supplier_name": supplier_name,
            "overall_risk_score": risk_data.get("overall_risk_score", 0),
            "risk_level": risk_data.get("risk_level", "UNKNOWN"),
            "disruption_probability_30d": risk_data.get("disruption_probability_30d", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "payload": risk_data,
        }
        self._publish(TOPICS["risk_events"], key=supplier_name, value=event)

        # Also publish to risk-scores topic for lightweight consumers
        score_event = {
            "supplier_name": supplier_name,
            "risk_score": risk_data.get("overall_risk_score", 0),
            "risk_level": risk_data.get("risk_level", "UNKNOWN"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._publish(TOPICS["risk_scores"], key=supplier_name, value=score_event)

    async def publish_alert(self, alert: dict):
        """Publish a high-severity disruption alert."""
        alert["timestamp"] = datetime.utcnow().isoformat()
        key = alert.get("event_type", "alert")
        self._publish(TOPICS["alerts"], key=key, value=alert)

        # Also publish critical/high alerts to risk-events for full traceability
        if alert.get("severity") in ("HIGH", "CRITICAL"):
            self._publish(TOPICS["risk_events"], key=key, value=alert)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _publish(self, topic: str, key: str, value: dict):
        if not self._producer:
            print(f"[Kafka Mock] → Topic: {topic} | Key: {key} | Value: {json.dumps(value)[:120]}...")
            return

        self._producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=json.dumps(value).encode("utf-8"),
            callback=self._delivery_report,
        )
        self._producer.poll(0)

    @staticmethod
    def _delivery_report(err, msg):
        if err:
            print(f"[Kafka] Delivery failed: {err}")
        else:
            print(f"[Kafka] Delivered → {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

    def flush(self):
        if self._producer:
            self._producer.flush()

    def close(self):
        self.flush()