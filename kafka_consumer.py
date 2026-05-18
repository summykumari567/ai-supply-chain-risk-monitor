"""
kafka_consumer.py — Kafka Risk Event Consumer

Consumes supply chain risk events and alerts from Kafka topics.
Run as a separate process alongside the FastAPI server.

Usage:
    python kafka_consumer.py

Subscribes to:
    supply-chain-risk-events
    supply-chain-alerts
    supplier-risk-scores
"""
import os
import json
import signal
import sys
from datetime import datetime

try:
    from confluent_kafka import Consumer, KafkaError, KafkaException
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("[Kafka] confluent-kafka not installed. Install it with: pip install confluent-kafka")


TOPICS = [
    "supply-chain-risk-events",
    "supply-chain-alerts",
    "supplier-risk-scores",
]

running = True


def handle_shutdown(sig, frame):
    global running
    print("\n[Consumer] Shutting down...")
    running = False


def process_risk_event(data: dict):
    supplier = data.get("supplier_name", "Unknown")
    score = data.get("overall_risk_score", 0)
    level = data.get("risk_level", "UNKNOWN")
    print(f"[RISK EVENT] {supplier} | Score: {score} | Level: {level}")

    # Hook: send to Slack, PagerDuty, database, etc.
    if level in ("HIGH", "CRITICAL"):
        trigger_alert(supplier, score, level)


def process_alert(data: dict):
    severity = data.get("severity", "UNKNOWN")
    regions = ", ".join(data.get("affected_regions", []))
    description = data.get("description", "")
    print(f"[ALERT] {severity} | Regions: {regions} | {description[:80]}")

    # Hook: push notification, dashboard update, email, etc.


def process_risk_score(data: dict):
    supplier = data.get("supplier_name", "Unknown")
    score = data.get("risk_score", 0)
    print(f"[RISK SCORE] {supplier}: {score}/100")

    # Hook: update database, trigger re-sourcing workflow, etc.


def trigger_alert(supplier: str, score: int, level: str):
    """Stub: replace with Slack webhook, PagerDuty, email, etc."""
    print(f"  ⚠️  ALERT TRIGGERED for {supplier} | Score: {score} | Level: {level}")


def run_consumer():
    if not KAFKA_AVAILABLE:
        print("[Consumer] Kafka not available. Exiting.")
        return

    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id = os.environ.get("KAFKA_CONSUMER_GROUP", "supply-chain-risk-monitor-group")

    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
    })

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    consumer.subscribe(TOPICS)
    print(f"[Consumer] Subscribed to: {', '.join(TOPICS)}")
    print(f"[Consumer] Group: {group_id} | Brokers: {bootstrap_servers}")

    try:
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            topic = msg.topic()
            try:
                data = json.loads(msg.value().decode("utf-8"))
            except json.JSONDecodeError as e:
                print(f"[Consumer] JSON parse error: {e}")
                continue

            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            print(f"[{timestamp}] Topic: {topic}")

            if topic == "supply-chain-risk-events":
                process_risk_event(data)
            elif topic == "supply-chain-alerts":
                process_alert(data)
            elif topic == "supplier-risk-scores":
                process_risk_score(data)

    finally:
        consumer.close()
        print("[Consumer] Closed.")


if __name__ == "__main__":
    run_consumer()