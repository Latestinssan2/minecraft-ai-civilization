"""Configuration loading for the AI engine."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


def _load_yaml(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class OllamaConfig:
    enabled: bool = True
    base_url: str = "http://localhost:11434"
    model: str = "qwen3:8b"
    timeout: int = 120
    max_concurrency: int = 1
    retry_attempts: int = 3
    retry_backoff_seconds: float = 2.0


@dataclass
class AgentConfig:
    agent_id: str
    name: str
    personality: str
    interests: List[str] = field(default_factory=list)
    provider: str = "ollama"
    model: str = ""


@dataclass
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    database_path: str = "data/civilization.db"
    log_level: str = "INFO"
    decision_interval_seconds: int = 30
    observation_radius: int = 32
    max_concurrent_ai: int = 1
    agent_count: int = 3
    use_mock_world: bool = True
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    agents: List[AgentConfig] = field(default_factory=list)
    civilization_name: str = "New Civilization"
    initial_instruction: str = ""


def load_config(path: str = "config/civilization.yaml") -> AppConfig:
    raw = _load_yaml(path)
    cfg = AppConfig()
    # top-level overrides
    for k in ("host", "port", "database_path", "log_level", "decision_interval_seconds",
              "observation_radius", "max_concurrent_ai", "agent_count", "civilization_name",
              "initial_instruction", "use_mock_world"):
        if k in raw:
            setattr(cfg, k, raw[k])
    # env overrides
    cfg.host = os.getenv("HOST", cfg.host)
    cfg.port = int(os.getenv("PORT", cfg.port))
    cfg.database_path = os.getenv("DATABASE_PATH", cfg.database_path)
    cfg.ollama.base_url = os.getenv("OLLAMA_BASE_URL", cfg.ollama.base_url)
    cfg.ollama.model = os.getenv("OLLAMA_MODEL", cfg.ollama.model)

    ai = raw.get("ai", {})
    prov = ai.get("providers", {}).get("ollama", {})
    if prov:
        cfg.ollama.enabled = prov.get("enabled", cfg.ollama.enabled)
        cfg.ollama.base_url = prov.get("base_url", cfg.ollama.base_url)
        cfg.ollama.model = prov.get("model", cfg.ollama.model)
        cfg.ollama.timeout = prov.get("timeout", cfg.ollama.timeout)
        cfg.ollama.max_concurrency = prov.get("max_concurrency", cfg.ollama.max_concurrency)
    if "default_provider" in ai:
        pass

    # agents
    agents_raw = raw.get("agents", [])
    cfg.agents = []
    for a in agents_raw:
        cfg.agents.append(AgentConfig(
            agent_id=a.get("agent_id", ""),
            name=a.get("name", ""),
            personality=a.get("personality", ""),
            interests=a.get("interests", []),
            provider=a.get("provider", "ollama"),
            model=a.get("model", ""),
        ))
    # fallback defaults for 3 agents if none configured
    if not cfg.agents:
        cfg.agents = _default_agents()
    return cfg


def _default_agents() -> List[AgentConfig]:
    return [
        AgentConfig(agent_id="agent_01", name="CHAIWALA", personality="Curious, ambitious, independent, strategic",
                    interests=["leadership", "exploration", "civilization planning", "social organization", "major construction"]),
        AgentConfig(agent_id="agent_02", name="Arin", personality="Intelligent, practical, patient, creative, organized",
                    interests=["construction", "engineering", "mining", "resource management", "infrastructure"]),
        AgentConfig(agent_id="agent_03", name="Mira", personality="Adventurous, curious, social, independent, adaptable",
                    interests=["exploration", "farming", "trading", "food production", "discovering new locations"]),
    ]
