"""
Neo4j graph service — replaces Zep Cloud with a self-hosted Neo4j backend.
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, List, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from ..config import Config

logger = logging.getLogger('nodera.neo4j_graph')

_CONNECT_RETRIES = 5
_CONNECT_BACKOFF = 3  # seconds between retries

_AUTH_HELP = (
    "Neo4j rejected the username/password (Neo.ClientError.Security.Unauthorized). "
    "Fix: (1) URI must be bolt://hostname:7687 — not olt://. "
    "(2) On the Neo4j Railway service use NEO4J_AUTH=neo4j/yourpassword. "
    "On Nodera Simulate set either the same NEO4J_AUTH (reference the Neo4j variable) OR "
    "NEO4J_PASSWORD equal to the part after the slash only. "
    "(3) If you changed NEO4J_AUTH after the DB first started, the password inside the "
    "persisted volume may still be the old one — reset the Neo4j password or recreate the volume."
)


def _is_neo4j_auth_failure(exc: BaseException) -> bool:
    s = str(exc).lower()
    code = getattr(exc, "code", None)
    code_s = str(code).lower() if code is not None else ""
    return (
        "unauthorized" in s
        or "authentication failure" in s
        or "security.unauthorized" in s
        or "unauthorized" in code_s
    )


class Neo4jGraphService:
    """Manages graph lifecycle and entity/relationship storage in Neo4j."""

    def __init__(self):
        uri = Config.NEO4J_URI
        user = Config.NEO4J_USER
        password = Config.NEO4J_PASSWORD
        auth_disabled = getattr(Config, "NEO4J_AUTH_DISABLED", False)

        if not auth_disabled and not password:
            raise ValueError("NEO4J_PASSWORD or NEO4J_AUTH is not configured")

        last_exc: BaseException | None = None
        auth_failed = False
        for attempt in range(1, _CONNECT_RETRIES + 1):
            try:
                if auth_disabled:
                    self.driver = GraphDatabase.driver(uri, auth=None)
                else:
                    self.driver = GraphDatabase.driver(uri, auth=(user, password))
                self.driver.verify_connectivity()
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                if _is_neo4j_auth_failure(exc):
                    auth_failed = True
                    logger.error("Neo4j authentication failed (not retrying): %s", exc)
                    break
                logger.warning(
                    "Neo4j connection attempt %d/%d failed: %s — retrying in %ds",
                    attempt,
                    _CONNECT_RETRIES,
                    exc,
                    _CONNECT_BACKOFF,
                )
                if attempt < _CONNECT_RETRIES:
                    time.sleep(_CONNECT_BACKOFF)

        if last_exc is not None:
            if auth_failed:
                raise ServiceUnavailable(_AUTH_HELP + f" Raw error: {last_exc}") from last_exc
            raise ServiceUnavailable(
                f"Cannot connect to Neo4j at {uri} after {_CONNECT_RETRIES} attempts. "
                f"Check that the Neo4j service is running and NEO4J_URI is correct. "
                f"Last error: {last_exc}"
            ) from last_exc

        self._ensure_schema()

    def close(self):
        self.driver.close()

    def _ensure_schema(self):
        with self.driver.session() as session:
            for cypher in [
                "CREATE CONSTRAINT mf_graph_id IF NOT EXISTS FOR (g:NDGraph) REQUIRE g.id IS UNIQUE",
                "CREATE CONSTRAINT mf_entity_uuid IF NOT EXISTS FOR (n:NDEntity) REQUIRE n.uuid IS UNIQUE",
                "CREATE INDEX mf_entity_name IF NOT EXISTS FOR (n:NDEntity) ON (n.name, n.graph_id)",
            ]:
                try:
                    session.run(cypher)
                except Exception:
                    pass  # constraint/index may already exist

    # ──────────────────────── Graph lifecycle ────────────────────────

    def create_graph(self, name: str) -> str:
        graph_id = f"nodera_{uuid.uuid4().hex[:16]}"
        with self.driver.session() as session:
            session.run(
                "CREATE (g:NDGraph {id: $id, name: $name, created_at: datetime()})",
                id=graph_id, name=name
            )
        logger.info(f"Graph created: {graph_id}")
        return graph_id

    def delete_graph(self, graph_id: str):
        with self.driver.session() as session:
            session.run(
                "MATCH (s:NDEntity {graph_id: $gid})-[r:ND_RELATES]->(t:NDEntity {graph_id: $gid}) DELETE r",
                gid=graph_id
            )
            session.run(
                "MATCH (g:NDGraph {id: $gid})-[r:ND_HAS_ENTITY]->() DELETE r",
                gid=graph_id
            )
            session.run(
                "MATCH (n:NDEntity {graph_id: $gid}) DELETE n",
                gid=graph_id
            )
            session.run(
                "MATCH (g:NDGraph {id: $gid}) DELETE g",
                gid=graph_id
            )
        logger.info(f"Graph deleted: {graph_id}")

    # ──────────────────────── Write ────────────────────────

    def add_entities_and_edges(
        self,
        graph_id: str,
        entities: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ):
        """Store extracted entities and relationships into Neo4j."""
        if not entities and not edges:
            return

        with self.driver.session() as session:
            # Upsert entities
            for entity in entities:
                name = (entity.get('name') or '').strip()
                if not name:
                    continue

                labels = entity.get('labels', [])
                if isinstance(labels, str):
                    labels = [labels]
                entity_type = entity.get('type', '')
                if entity_type and entity_type not in labels:
                    labels.append(entity_type)
                if 'Entity' not in labels:
                    labels = ['Entity'] + labels

                session.run(
                    """
                    MATCH (g:NDGraph {id: $gid})
                    MERGE (n:NDEntity {name: $name, graph_id: $gid})
                    ON CREATE SET
                        n.uuid       = $uuid,
                        n.summary    = $summary,
                        n.labels     = $labels,
                        n.attributes = $attributes,
                        n.created_at = datetime()
                    ON MATCH SET
                        n.summary    = CASE WHEN $summary <> '' THEN $summary ELSE n.summary END,
                        n.labels     = $labels
                    WITH n, g
                    MERGE (g)-[:ND_HAS_ENTITY]->(n)
                    """,
                    gid=graph_id,
                    name=name,
                    uuid=str(uuid.uuid4()),
                    summary=entity.get('summary', ''),
                    labels=json.dumps(labels),
                    attributes=json.dumps(entity.get('attributes', {})),
                )

            # Create relationship edges
            for edge in edges:
                src = (edge.get('source') or '').strip()
                tgt = (edge.get('target') or '').strip()
                if not src or not tgt:
                    continue

                session.run(
                    """
                    MATCH (s:NDEntity {name: $src, graph_id: $gid})
                    MATCH (t:NDEntity {name: $tgt, graph_id: $gid})
                    CREATE (s)-[r:ND_RELATES {
                        uuid:       $uuid,
                        name:       $name,
                        fact:       $fact,
                        graph_id:   $gid,
                        created_at: datetime(),
                        valid_at:   datetime()
                    }]->(t)
                    """,
                    gid=graph_id,
                    src=src,
                    tgt=tgt,
                    uuid=str(uuid.uuid4()),
                    name=edge.get('name', 'relates_to'),
                    fact=edge.get('fact', ''),
                )

    # ──────────────────────── Read ────────────────────────

    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (g:NDGraph {id: $gid})-[:ND_HAS_ENTITY]->(n:NDEntity)
                RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary,
                       n.labels AS labels, n.attributes AS attributes
                """,
                gid=graph_id,
            )
            return [self._parse_node_record(r) for r in result]

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:NDEntity {graph_id: $gid})-[r:ND_RELATES {graph_id: $gid}]->(t:NDEntity)
                RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                       s.uuid AS source_uuid, t.uuid AS target_uuid,
                       s.name AS source_name, t.name AS target_name,
                       toString(r.created_at) AS created_at,
                       toString(r.valid_at)   AS valid_at,
                       r.invalid_at           AS invalid_at,
                       r.expired_at           AS expired_at
                """,
                gid=graph_id,
            )
            return [self._parse_edge_record(r) for r in result]

    def get_node_detail(self, node_uuid: str) -> Optional[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n:NDEntity {uuid: $uuid})
                RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary,
                       n.labels AS labels, n.attributes AS attributes
                """,
                uuid=node_uuid,
            )
            record = result.single()
            return self._parse_node_record(record) if record else None

    def get_node_edges(self, node_uuid: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n:NDEntity {uuid: $uuid})-[r:ND_RELATES]-(other:NDEntity)
                RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                       CASE WHEN startNode(r).uuid = $uuid
                            THEN $uuid ELSE other.uuid END AS source_uuid,
                       CASE WHEN startNode(r).uuid = $uuid
                            THEN other.uuid ELSE $uuid END AS target_uuid
                """,
                uuid=node_uuid,
            )
            edges = []
            for r in result:
                edges.append({
                    'uuid':             r['uuid'] or '',
                    'name':             r['name'] or '',
                    'fact':             r['fact'] or '',
                    'source_node_uuid': r['source_uuid'] or '',
                    'target_node_uuid': r['target_uuid'] or '',
                    'attributes':       {},
                })
            return edges

    # ──────────────────────── Search ────────────────────────

    def search_graph(
        self,
        graph_id: str,
        query: str,
        limit: int = 10,
        scope: str = "edges",
    ) -> Dict[str, Any]:
        """
        Keyword search over edges (facts) and nodes (summaries/names).
        Falls back to multi-keyword OR search when the full query has no hits.
        """
        query_lower = query.lower()
        keywords = [
            w.strip()
            for w in query_lower.replace(',', ' ').replace('，', ' ').split()
            if len(w.strip()) > 1
        ]

        facts: List[str] = []
        edges_out: List[Dict] = []
        nodes_out: List[Dict] = []

        with self.driver.session() as session:
            if scope in ("edges", "both"):
                # Full-query match first
                rows = session.run(
                    """
                    MATCH (s:NDEntity {graph_id: $gid})-[r:ND_RELATES {graph_id: $gid}]->(t:NDEntity)
                    WHERE toLower(r.fact) CONTAINS $q OR toLower(r.name) CONTAINS $q
                    RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                           s.uuid AS src_uuid, t.uuid AS tgt_uuid,
                           s.name AS src_name, t.name AS tgt_name
                    LIMIT $lim
                    """,
                    gid=graph_id, q=query_lower, lim=limit,
                )
                for r in rows:
                    fact = r['fact'] or ''
                    if fact and fact not in facts:
                        facts.append(fact)
                    edges_out.append({
                        'uuid':             r['uuid'],
                        'name':             r['name'],
                        'fact':             fact,
                        'source_node_uuid': r['src_uuid'],
                        'target_node_uuid': r['tgt_uuid'],
                        'source_node_name': r['src_name'],
                        'target_node_name': r['tgt_name'],
                    })

                # Keyword fallback for more coverage
                if len(facts) < limit:
                    for kw in keywords[:4]:
                        kw_rows = session.run(
                            """
                            MATCH (s:NDEntity {graph_id: $gid})-[r:ND_RELATES {graph_id: $gid}]->(t:NDEntity)
                            WHERE toLower(r.fact) CONTAINS $kw
                            RETURN r.fact AS fact LIMIT $lim
                            """,
                            gid=graph_id, kw=kw, lim=limit,
                        )
                        for r in kw_rows:
                            if r['fact'] and r['fact'] not in facts:
                                facts.append(r['fact'])

            if scope in ("nodes", "both"):
                rows = session.run(
                    """
                    MATCH (g:NDGraph {id: $gid})-[:ND_HAS_ENTITY]->(n:NDEntity)
                    WHERE toLower(n.name) CONTAINS $q OR toLower(n.summary) CONTAINS $q
                    RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary,
                           n.labels AS labels
                    LIMIT $lim
                    """,
                    gid=graph_id, q=query_lower, lim=limit,
                )
                for r in rows:
                    labels = self._parse_labels(r['labels'])
                    nodes_out.append({
                        'uuid':    r['uuid'],
                        'name':    r['name'],
                        'labels':  labels,
                        'summary': r['summary'] or '',
                    })
                    summary = r['summary'] or ''
                    if summary:
                        text = f"[{r['name']}]: {summary}"
                        if text not in facts:
                            facts.append(text)

        return {
            'facts':       facts[:limit],
            'edges':       edges_out[:limit],
            'nodes':       nodes_out[:limit],
            'query':       query,
            'total_count': len(facts),
        }

    # ──────────────────────── Info ────────────────────────

    def get_graph_info(self, graph_id: str) -> Dict[str, Any]:
        with self.driver.session() as session:
            counts = session.run(
                """
                MATCH (g:NDGraph {id: $gid})
                OPTIONAL MATCH (g)-[:ND_HAS_ENTITY]->(n:NDEntity)
                OPTIONAL MATCH (n)-[r:ND_RELATES {graph_id: $gid}]->(:NDEntity)
                RETURN COUNT(DISTINCT n) AS node_count,
                       COUNT(DISTINCT r) AS edge_count
                """,
                gid=graph_id,
            ).single()

            label_rows = session.run(
                "MATCH (g:NDGraph {id: $gid})-[:ND_HAS_ENTITY]->(n:NDEntity) RETURN n.labels AS labels",
                gid=graph_id,
            )
            entity_types: set = set()
            for r in label_rows:
                for lbl in self._parse_labels(r['labels']):
                    if lbl not in ('Entity', 'Node'):
                        entity_types.add(lbl)

        return {
            'graph_id':     graph_id,
            'node_count':   counts['node_count'] if counts else 0,
            'edge_count':   counts['edge_count'] if counts else 0,
            'entity_types': list(entity_types),
        }

    # ──────────────────────── Helpers ────────────────────────

    @staticmethod
    def _parse_labels(raw) -> List[str]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return ['Entity']
        return ['Entity']

    @staticmethod
    def _parse_attributes(raw) -> Dict:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return {}
        return {}

    def _parse_node_record(self, r) -> Dict[str, Any]:
        return {
            'uuid':       r['uuid'] or '',
            'name':       r['name'] or '',
            'summary':    r['summary'] or '',
            'labels':     self._parse_labels(r['labels']),
            'attributes': self._parse_attributes(r['attributes']),
        }

    @staticmethod
    def _parse_edge_record(r) -> Dict[str, Any]:
        return {
            'uuid':             r['uuid'] or '',
            'name':             r['name'] or '',
            'fact':             r['fact'] or '',
            'source_node_uuid': r['source_uuid'] or '',
            'target_node_uuid': r['target_uuid'] or '',
            'source_node_name': r['source_name'] or '',
            'target_node_name': r['target_name'] or '',
            'created_at':       r['created_at'],
            'valid_at':         r['valid_at'],
            'invalid_at':       r['invalid_at'],
            'expired_at':       r['expired_at'],
        }
