"""Provider abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ProviderResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    model: str = ""
    raw: Optional[Dict[str, Any]] = None


class ProviderError(Exception):
    pass


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, model: Optional[str] = None,
                 json_mode: bool = True, timeout: Optional[int] = None) -> ProviderResponse:
        ...

    @abstractmethod
    def list_models(self) -> List[str]:
        ...
