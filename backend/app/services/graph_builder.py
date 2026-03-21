"""
图谱构建服务
使用Neo4j作为图数据库，LLM自动提取实体和关系
"""

import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from ..models.task import TaskManager, TaskStatus
from .neo4j_graph import Neo4jGraphService
from .entity_extractor import EntityExtractor
from .text_processor import TextProcessor
from ..utils.logger import get_logger

logger = get_logger('nodera.graph_builder')


@dataclass
class GraphInfo:
    """图谱摘要信息"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id":     self.graph_id,
            "node_count":   self.node_count,
            "edge_count":   self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    图谱构建服务 — Neo4j版本
    流程:
      1. 在Neo4j中创建图谱节点
      2. 文本分块
      3. 每批文本块通过LLM提取实体/关系
      4. 存储到Neo4j
      5. 返回图谱摘要
    """

    def __init__(self, api_key: Optional[str] = None):
        # api_key parameter kept for backward compatibility but ignored
        self.client = Neo4jGraphService()
        self.extractor = EntityExtractor()
        self.task_manager = TaskManager()
        self._ontology: Dict[str, Any] = {}

    # ──────────────────────── Public API ────────────────────────

    def create_graph(self, name: str) -> str:
        """Create a new graph and return its ID."""
        return self.client.create_graph(name)

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Store the ontology for use during entity extraction (in-memory only)."""
        self._ontology = ontology or {}

    def add_text_batches(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None,
    ) -> List[str]:
        """
        Extract entities/edges from chunks (in batches) and store in Neo4j.

        Returns a list of placeholder IDs (one per chunk) — used only for
        progress tracking, not for Zep-style episode polling.
        """
        total = len(chunks)
        placeholder_ids = []

        for i in range(0, total, batch_size):
            batch = chunks[i: i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            if progress_callback:
                progress = (i + len(batch)) / total
                progress_callback(
                    f"处理第 {batch_num}/{total_batches} 批 ({len(batch)} 块)...",
                    progress,
                )

            # Extract from each chunk and accumulate before writing
            all_entities: List[Dict] = []
            all_edges: List[Dict] = []
            for chunk in batch:
                result = self.extractor.extract(chunk, self._ontology)
                all_entities.extend(result.get('entities', []))
                all_edges.extend(result.get('edges', []))

            # Write batch to Neo4j
            try:
                self.client.add_entities_and_edges(graph_id, all_entities, all_edges)
            except Exception as exc:
                logger.warning(f"批次 {batch_num} 存储失败: {exc}")

            placeholder_ids.extend([f"chunk_{i + j}" for j in range(len(batch))])

        return placeholder_ids

    def _wait_for_episodes(
        self,
        episode_uuids: List[str],
        progress_callback: Optional[Callable] = None,
        timeout: int = 600,
    ):
        """No-op: Neo4j writes are synchronous, no polling needed."""
        if progress_callback:
            progress_callback("图谱数据已写入Neo4j", 1.0)

    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """Return full graph data (nodes + edges) for a given graph."""
        nodes_data = self.client.get_all_nodes(graph_id)
        edges_data = self.client.get_all_edges(graph_id)

        node_map = {n['uuid']: n['name'] for n in nodes_data}

        nodes_out = []
        for n in nodes_data:
            nodes_out.append({
                "uuid":       n['uuid'],
                "name":       n['name'],
                "labels":     n['labels'],
                "summary":    n['summary'],
                "attributes": n['attributes'],
                "created_at": None,
            })

        edges_out = []
        for e in edges_data:
            edges_out.append({
                "uuid":             e['uuid'],
                "name":             e['name'],
                "fact":             e['fact'],
                "fact_type":        e['name'],
                "source_node_uuid": e['source_node_uuid'],
                "target_node_uuid": e['target_node_uuid'],
                "source_node_name": e.get('source_node_name') or node_map.get(e['source_node_uuid'], ''),
                "target_node_name": e.get('target_node_name') or node_map.get(e['target_node_uuid'], ''),
                "attributes":       {},
                "created_at":       e.get('created_at'),
                "valid_at":         e.get('valid_at'),
                "invalid_at":       e.get('invalid_at'),
                "expired_at":       e.get('expired_at'),
                "episodes":         [],
            })

        return {
            "graph_id":   graph_id,
            "nodes":      nodes_out,
            "edges":      edges_out,
            "node_count": len(nodes_out),
            "edge_count": len(edges_out),
        }

    def delete_graph(self, graph_id: str):
        """Delete a graph and all its entities/edges."""
        self.client.delete_graph(graph_id)

    # ──────────────────────── Async wrapper ────────────────────────

    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "Nodera Simulate Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3,
    ) -> str:
        """Kick off an async graph-build task and return the task ID."""
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name":  graph_name,
                "chunk_size":  chunk_size,
                "text_length": len(text),
            },
        )
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size),
            daemon=True,
        )
        thread.start()
        return task_id

    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int,
    ):
        try:
            self.task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=5, message="Starting graph build…")

            graph_id = self.create_graph(graph_name)
            self.task_manager.update_task(task_id, progress=10, message=f"Graph created: {graph_id}")

            self.set_ontology(graph_id, ontology)
            self.task_manager.update_task(task_id, progress=15, message="本体已设置")

            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(task_id, progress=20, message=f"文本已分割为 {total_chunks} 块")

            self.add_text_batches(
                graph_id, chunks, batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id, progress=20 + int(prog * 70), message=msg
                ),
            )

            info = self.client.get_graph_info(graph_id)
            self.task_manager.complete_task(task_id, {
                "graph_id":         graph_id,
                "graph_info":       info,
                "chunks_processed": total_chunks,
            })

        except Exception as exc:
            import traceback
            self.task_manager.fail_task(task_id, f"{exc}\n{traceback.format_exc()}")
