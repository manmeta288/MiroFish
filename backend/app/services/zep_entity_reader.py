"""
实体读取与过滤服务
从Neo4j图谱读取节点，筛选出符合预定义实体类型的节点
（原 ZepEntityReader — 类名保留以保证向下兼容）
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

from .neo4j_graph import Neo4jGraphService
from ..utils.logger import get_logger

logger = get_logger('mirofish.entity_reader')


@dataclass
class EntityNode:
    """实体节点数据结构"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid":          self.uuid,
            "name":          self.name,
            "labels":        self.labels,
            "summary":       self.summary,
            "attributes":    self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }

    def get_entity_type(self) -> Optional[str]:
        for label in self.labels:
            if label not in ("Entity", "Node"):
                return label
        return None


@dataclass
class FilteredEntities:
    """过滤后的实体集合"""
    entities: List[EntityNode]
    entity_types: Set[str]
    total_count: int
    filtered_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities":      [e.to_dict() for e in self.entities],
            "entity_types":  list(self.entity_types),
            "total_count":   self.total_count,
            "filtered_count": self.filtered_count,
        }


class ZepEntityReader:
    """
    实体读取与过滤服务（Neo4j后端）

    主要功能：
    1. 从Neo4j图谱读取所有节点
    2. 筛选符合预定义实体类型的节点
    3. 获取每个实体的相关边和关联节点信息
    """

    def __init__(self, api_key: Optional[str] = None):
        # api_key kept for backward compatibility, ignored
        self.client = Neo4jGraphService()

    # ──────────────────────── Raw data ────────────────────────

    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        nodes = self.client.get_all_nodes(graph_id)
        logger.info(f"获取 {len(nodes)} 个节点 (graph={graph_id})")
        return nodes

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        edges = self.client.get_all_edges(graph_id)
        logger.info(f"获取 {len(edges)} 条边 (graph={graph_id})")
        return edges

    def get_node_edges(self, node_uuid: str) -> List[Dict[str, Any]]:
        try:
            return self.client.get_node_edges(node_uuid)
        except Exception as exc:
            logger.warning(f"获取节点 {node_uuid} 的边失败: {exc}")
            return []

    # ──────────────────────── Filtering ────────────────────────

    def filter_defined_entities(
        self,
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True,
    ) -> FilteredEntities:
        """
        筛选符合预定义实体类型的节点。

        筛选逻辑：
        - Labels 只含 'Entity'/'Node' 的节点 → 跳过
        - Labels 含其他标签的节点 → 保留（可选按 defined_entity_types 进一步过滤）
        """
        logger.info(f"筛选图谱实体: graph={graph_id}, types={defined_entity_types}")

        all_nodes = self.get_all_nodes(graph_id)
        all_edges = self.get_all_edges(graph_id) if enrich_with_edges else []
        node_map = {n["uuid"]: n for n in all_nodes}

        filtered: List[EntityNode] = []
        entity_types_found: Set[str] = set()

        for node in all_nodes:
            labels = node.get("labels", [])
            custom = [l for l in labels if l not in ("Entity", "Node")]
            if not custom:
                continue

            if defined_entity_types:
                matching = [l for l in custom if l in defined_entity_types]
                if not matching:
                    continue
                entity_type = matching[0]
            else:
                entity_type = custom[0]

            entity_types_found.add(entity_type)

            entity = EntityNode(
                uuid=node["uuid"],
                name=node["name"],
                labels=labels,
                summary=node["summary"],
                attributes=node["attributes"],
            )

            if enrich_with_edges:
                related_edges = []
                related_node_uuids: Set[str] = set()

                for edge in all_edges:
                    if edge["source_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction":        "outgoing",
                            "edge_name":        edge["name"],
                            "fact":             edge["fact"],
                            "target_node_uuid": edge["target_node_uuid"],
                        })
                        related_node_uuids.add(edge["target_node_uuid"])
                    elif edge["target_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction":        "incoming",
                            "edge_name":        edge["name"],
                            "fact":             edge["fact"],
                            "source_node_uuid": edge["source_node_uuid"],
                        })
                        related_node_uuids.add(edge["source_node_uuid"])

                entity.related_edges = related_edges
                entity.related_nodes = [
                    {
                        "uuid":    node_map[u]["uuid"],
                        "name":    node_map[u]["name"],
                        "labels":  node_map[u]["labels"],
                        "summary": node_map[u].get("summary", ""),
                    }
                    for u in related_node_uuids
                    if u in node_map
                ]

            filtered.append(entity)

        logger.info(
            f"筛选完成: 总节点 {len(all_nodes)}, 符合条件 {len(filtered)}, "
            f"实体类型: {entity_types_found}"
        )
        return FilteredEntities(
            entities=filtered,
            entity_types=entity_types_found,
            total_count=len(all_nodes),
            filtered_count=len(filtered),
        )

    # ──────────────────────── Single-entity helpers ────────────────────────

    def get_entity_with_context(
        self, graph_id: str, entity_uuid: str
    ) -> Optional[EntityNode]:
        node = self.client.get_node_detail(entity_uuid)
        if not node:
            return None

        edges = self.get_node_edges(entity_uuid)
        all_nodes = self.get_all_nodes(graph_id)
        node_map = {n["uuid"]: n for n in all_nodes}

        related_edges = []
        related_node_uuids: Set[str] = set()

        for edge in edges:
            if edge["source_node_uuid"] == entity_uuid:
                related_edges.append({
                    "direction":        "outgoing",
                    "edge_name":        edge["name"],
                    "fact":             edge["fact"],
                    "target_node_uuid": edge["target_node_uuid"],
                })
                related_node_uuids.add(edge["target_node_uuid"])
            else:
                related_edges.append({
                    "direction":        "incoming",
                    "edge_name":        edge["name"],
                    "fact":             edge["fact"],
                    "source_node_uuid": edge["source_node_uuid"],
                })
                related_node_uuids.add(edge["source_node_uuid"])

        related_nodes = [
            {
                "uuid":    node_map[u]["uuid"],
                "name":    node_map[u]["name"],
                "labels":  node_map[u]["labels"],
                "summary": node_map[u].get("summary", ""),
            }
            for u in related_node_uuids
            if u in node_map
        ]

        return EntityNode(
            uuid=node["uuid"],
            name=node["name"],
            labels=node["labels"],
            summary=node["summary"],
            attributes=node["attributes"],
            related_edges=related_edges,
            related_nodes=related_nodes,
        )

    def get_entities_by_type(
        self,
        graph_id: str,
        entity_type: str,
        enrich_with_edges: bool = True,
    ) -> List[EntityNode]:
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges,
        )
        return result.entities
