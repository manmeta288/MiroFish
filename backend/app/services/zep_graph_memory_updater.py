"""
图谱记忆更新服务 — 已禁用（Zep已迁移至Neo4j）
保留类名和接口以保证向下兼容，所有方法为空操作。
"""

from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentActivity:
    """Agent活动记录（保留数据结构）"""
    simulation_id: str
    agent_name: str
    action_type: str
    platform: str
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ZepGraphMemoryUpdater:
    """图谱记忆更新器（No-op stub）"""

    def __init__(self, graph_id: str, api_key: Optional[str] = None):
        self.graph_id = graph_id

    def start(self):
        pass

    def stop(self):
        pass

    def add_activity(self, activity: AgentActivity):
        pass

    def set_graph_id(self, graph_id: str):
        self.graph_id = graph_id


class ZepGraphMemoryManager:
    """图谱记忆管理器（No-op stub）"""

    _updaters: Dict[str, ZepGraphMemoryUpdater] = {}

    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> ZepGraphMemoryUpdater:
        updater = ZepGraphMemoryUpdater(graph_id)
        cls._updaters[simulation_id] = updater
        return updater

    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[ZepGraphMemoryUpdater]:
        return cls._updaters.get(simulation_id)

    @classmethod
    def stop_updater(cls, simulation_id: str):
        cls._updaters.pop(simulation_id, None)

    @classmethod
    def stop_all(cls):
        cls._updaters.clear()
