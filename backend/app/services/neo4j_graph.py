"""
Neo4j图谱服务
替代Zep Cloud，使用Neo4j作为图数据库后端
"""

import uuid
import json
import logging
from typing import Dict, Any, List, Optional

from neo4j import GraphDatabase

from ..config import Config

logger = logging.getLogger('mirofish.neo4j_graph')


class Neo4jGraphService:
    """
    Neo4j图谱服务
    负责图谱的创建、实体/关系存储、搜索和删除
    """

    def __init__(self):
        uri = Config.NEO4J_URI
        user = Config.NEO4J_USER
        password = Config.NEO4J_PASSWORD
        if not password:
            raise ValueError("NEO4J_PASSWORD 未配置")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_schema()

    def close(self):
        self.driver.close()

    def _ensure_schema(self):
        with self.driver.session() as session:
            for cypher in [
                "CREATE CONSTRAINT mf_graph_id IF NOT EXISTS FOR (g:MFGraph) REQUIRE g.id IS UNIQUE",
                "CREATE CONSTRAINT mf_entity_uuid IF NOT EXISTS FOR (n:MFEntity) REQUIRE n.uuid IS UNIQUE",
                "CREATE INDEX mf_entity_name IF NOT EXISTS FOR (n:MFEntity) ON (n.name, n.graph_id)",
            ]:
                try:
                    session.run(cypher)
                except Exception:
                    pass  # constraint/index may already exist

    # ──────────────────────── Graph lifecycle ────────────────────────

    def create_graph(self, name: str) -> str:
        graph_id = f"mirofish_{uuid.uuid4().hex[:16]}"
        with self.driver.session() as session:
            session.run(
                "CREATE (g:MFGraph {id: $id, name: $name, created_at: datetime()})",
                id=graph_id, name=name
            )
        logger.info(f"图谱已创建: {graph_id}")
        return graph_id

    def delete_graph(self, graph_id: str):
        with self.driver.session() as session:
            session.run(
                "MATCH (s:MFEntity {graph_id: $gid})-[r:MF_RELATES]->(t:MFEntity {graph_id: $gid}) DELETE r",
                gid=graph_id
            )
            session.run(
                "MATCH (g:MFGraph {id: $gid})-[r:MF_HAS_ENTITY]->() DELETE r",
                gid=graph_id
            )
            session.run(
                "MATCH (n:MFEntity {graph_id: $gid}) DELETE n",
                gid=graph_id
            )
            session.run(
                "MATCH (g:MFGraph {id: $gid}) DELETE g",
                gid=graph_id
            )
        logger.info(f"图谱已删除: {graph_id}")

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
                    MATCH (g:MFGraph {id: $gid})
                    MERGE (n:MFEntity {name: $name, graph_id: $gid})
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
                    MERGE (g)-[:MF_HAS_ENTITY]->(n)
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
                    MATCH (s:MFEntity {name: $src, graph_id: $gid})
                    MATCH (t:MFEntity {name: $tgt, graph_id: $gid})
                    CREATE (s)-[r:MF_RELATES {
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
                MATCH (g:MFGraph {id: $gid})-[:MF_HAS_ENTITY]->(n:MFEntity)
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
                MATCH (s:MFEntity {graph_id: $gid})-[r:MF_RELATES {graph_id: $gid}]->(t:MFEntity)
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
                MATCH (n:MFEntity {uuid: $uuid})
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
                MATCH (n:MFEntity {uuid: $uuid})-[r:MF_RELATES]-(other:MFEntity)
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
                    MATCH (s:MFEntity {graph_id: $gid})-[r:MF_RELATES {graph_id: $gid}]->(t:MFEntity)
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
                            MATCH (s:MFEntity {graph_id: $gid})-[r:MF_RELATES {graph_id: $gid}]->(t:MFEntity)
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
                    MATCH (g:MFGraph {id: $gid})-[:MF_HAS_ENTITY]->(n:MFEntity)
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
                MATCH (g:MFGraph {id: $gid})
                OPTIONAL MATCH (g)-[:MF_HAS_ENTITY]->(n:MFEntity)
                OPTIONAL MATCH (n)-[r:MF_RELATES {graph_id: $gid}]->(:MFEntity)
                RETURN COUNT(DISTINCT n) AS node_count,
                       COUNT(DISTINCT r) AS edge_count
                """,
                gid=graph_id,
            ).single()

            label_rows = session.run(
                "MATCH (g:MFGraph {id: $gid})-[:MF_HAS_ENTITY]->(n:MFEntity) RETURN n.labels AS labels",
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
