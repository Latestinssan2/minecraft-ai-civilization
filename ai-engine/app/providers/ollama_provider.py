"""Ollama provider implementation."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import OllamaConfig
from app.providers.base import BaseProvider, ProviderError, ProviderResponse


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, cfg: OllamaConfig):
        self.cfg = cfg
        self.base_url = cfg.base_url.rstrip("/")
        self.model = cfg.model

    def health_check(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=5.0) as c:
                r = c.get(f"{self.base_url}/api/tags")
                r.raise_for_status()
                data = r.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status": "ok",
                    "base_url": self.base_url,
                    "configured_model": self.model,
                    "available_models": models,
                    "model_available": self.model in models,
                }
        except Exception as e:
            return {
                "status": "error",
                "base_url": self.base_url,
                "configured_model": self.model,
                "available_models": [],
                "model_available": False,
                "error": str(e),
            }

    def list_models(self) -> List[str]:
        hc = self.health_check()
        return hc.get("available_models", [])

    def generate(self, system_prompt: str, user_prompt: str, model: Optional[str] = None,
                 json_mode: bool = True, timeout: Optional[int] = None) -> ProviderResponse:
        m = model or self.model
        to = timeout or self.cfg.timeout
        payload: Dict[str, Any] = {
            "model": m,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"
        t0 = time.time()
        last_err = None
        attempts = self.cfg.retry_attempts
        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(timeout=to) as c:
                    r = c.post(f"{self.base_url}/api/chat", json=payload)
                    r.raise_for_status()
                    data = r.json()
                break
            except Exception as e:
                last_err = e
                if attempt < attempts:
                    time.sleep(self.cfg.retry_backoff_seconds * attempt)
        else:
            raise ProviderError(f"Ollama request failed after {attempts} attempts: {last_err}")
        latency = int((time.time() - t0) * 1000)
        msg = data.get("message", {}) or {}
        text = msg.get("content", "") or ""
        # token counts (ollama provides eval_count/prompt_eval_count)
        pt = data.get("prompt_eval_count", 0) or 0
        ct = data.get("eval_count", 0) or 0
        return ProviderResponse(text=text, prompt_tokens=pt, completion_tokens=ct, latency_ms=latency, model=m, raw=data)
