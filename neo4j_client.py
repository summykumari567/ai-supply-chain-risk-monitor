"""
neo4j_client.py — Neo4j Supply Chain Graph Client

Graph schema:
  Nodes:  Supplier, Country, Product, Category
  Edges:  SUPPLIES, LOCATED_IN, PRODUCES, ALTERNATIVE_FOR, TIER_OF

Stores the full multi-tier supplier network and enables:
  - Graph traversal (find all sub-suppliers of a Tier 1 supplier)
  - Risk propagation queries
  - Alternative supplier discovery
"""
import os
from typing import Optional

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


class Neo4jClient:
    def __init__(self):
        self.uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.environ.get("NEO4J_USER", "neo4j")
        self.password = os.environ.get("NEO4J_PASSWORD", "password")
        self._driver = None
        self._connect()

    def _connect(self):
        if not NEO4J_AVAILABLE:
            print("[Neo4j] neo4j driver not installed — running in mock mode")
            return
        try:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            self._driver.verify_connectivity()
            self._create_constraints()
            print("[Neo4j] Connected successfully")
        except Exception as e:
            print(f"[Neo4j] Connection failed (mock mode): {e}")
            self._driver = None

    def is_connected(self) -> bool:
        return self._driver is not None

    def _create_constraints(self):
        if not self._driver:
            return
        with self._driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Supplier) REQUIRE s.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE")

    # ── Supplier CRUD ──────────────────────────────────────────────────────────

    def create_supplier(self, data: dict) -> dict:
        if not self._driver:
            return {**data, "id": f"mock-{data['name']}", "status": "mock"}

        with self._driver.session() as session:
            result = session.run(
                """
                MERGE (s:Supplier {name: $name})
                SET s.country = $country,
                    s.category = $category,
                    s.tier = $tier,
                    s.annual_spend_usd = $annual_spend_usd,
                    s.products = $products,
                    s.created_at = datetime()
                MERGE (c:Country {name: $country})
                MERGE (s)-[:LOCATED_IN]->(c)
                RETURN s
                """,
                name=data["name"],
                country=data.get("country", "Unknown"),
                category=data.get("category", ""),
                tier=data.get("tier", 1),
                annual_spend_usd=data.get("annual_spend_usd"),
                products=data.get("products", []),
            )
            record = result.single()
            return dict(record["s"]) if record else data

    def get_all_suppliers(self) -> list[dict]:
        if not self._driver:
            return self._mock_suppliers()

        with self._driver.session() as session:
            result = session.run(
                "MATCH (s:Supplier) RETURN s ORDER BY s.tier, s.name LIMIT 100"
            )
            return [dict(r["s"]) for r in result]

    def find_alternatives(self, supplier_name: str, category: str) -> list[dict]:
        """Find alternative suppliers in same category, different country."""
        if not self._driver:
            return []

        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (s:Supplier {name: $name})
                MATCH (alt:Supplier)
                WHERE alt.category = $category
                  AND alt.name <> $name
                  AND alt.country <> s.country
                RETURN alt
                ORDER BY alt.tier
                LIMIT 10
                """,
                name=supplier_name,
                category=category,
            )
            return [dict(r["alt"]) for r in result]

    def add_alternative_relationship(self, supplier_a: str, supplier_b: str, reason: str = ""):
        """Create ALTERNATIVE_FOR relationship between two suppliers."""
        if not self._driver:
            return

        with self._driver.session() as session:
            session.run(
                """
                MATCH (a:Supplier {name: $a}), (b:Supplier {name: $b})
                MERGE (a)-[r:ALTERNATIVE_FOR]->(b)
                SET r.reason = $reason, r.created_at = datetime()
                """,
                a=supplier_a, b=supplier_b, reason=reason,
            )

    def get_graph_data(self) -> dict:
        """Return nodes + edges for frontend graph visualization."""
        if not self._driver:
            return self._mock_graph()

        with self._driver.session() as session:
            nodes_result = session.run(
                "MATCH (s:Supplier) RETURN s.name AS id, s.country AS country, "
                "s.category AS category, s.tier AS tier LIMIT 100"
            )
            edges_result = session.run(
                """
                MATCH (a:Supplier)-[r]->(b:Supplier)
                RETURN a.name AS source, type(r) AS type, b.name AS target
                LIMIT 200
                """
            )
            nodes = [{"id": r["id"], "country": r["country"],
                      "category": r["category"], "tier": r["tier"]} for r in nodes_result]
            edges = [{"source": r["source"], "type": r["type"],
                      "target": r["target"]} for r in edges_result]
            return {"nodes": nodes, "edges": edges}

    def close(self):
        if self._driver:
            self._driver.close()

    # ── Mock data (when Neo4j is not available) ────────────────────────────────

    @staticmethod
    def _mock_suppliers() -> list[dict]:
        return [
            {"name": "TSMC", "country": "Taiwan", "category": "semiconductors", "tier": 1},
            {"name": "Samsung Electronics", "country": "South Korea", "category": "semiconductors", "tier": 1},
            {"name": "Intel Foundry", "country": "USA", "category": "semiconductors", "tier": 1},
            {"name": "Foxconn", "country": "China", "category": "electronics assembly", "tier": 1},
            {"name": "Flex Ltd", "country": "Singapore", "category": "electronics assembly", "tier": 1},
        ]

    @staticmethod
    def _mock_graph() -> dict:
        return {
            "nodes": [
                {"id": "TSMC", "country": "Taiwan", "category": "semiconductors", "tier": 1},
                {"id": "Samsung", "country": "South Korea", "category": "semiconductors", "tier": 1},
                {"id": "Foxconn", "country": "China", "category": "assembly", "tier": 1},
                {"id": "ASML", "country": "Netherlands", "category": "equipment", "tier": 2},
            ],
            "edges": [
                {"source": "ASML", "type": "SUPPLIES", "target": "TSMC"},
                {"source": "ASML", "type": "SUPPLIES", "target": "Samsung"},
                {"source": "TSMC", "type": "ALTERNATIVE_FOR", "target": "Samsung"},
            ],
        }