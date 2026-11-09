"""Abstraction for Minecraft world interaction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class WorldBridge(ABC):
    @abstractmethod
    def get_observation(self, agent_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def execute_action(self, agent_id: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        ...
