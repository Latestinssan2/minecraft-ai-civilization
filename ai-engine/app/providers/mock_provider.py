"""Mock provider for tests / offline development. Not used by default."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from app.providers.base import BaseProvider, ProviderResponse


class MockProvider(BaseProvider):
    name = "mock"

    def __init__(self, canned: Optional[Dict[str, Any]] = None):
        self.canned = canned or {}

    def health_check(self) -> Dict[str, Any]:
        return {"status": "ok", "base_url": "mock", "configured_model": "mock", "available_models": ["mock"], "model_available": True}

    def list_models(self) -> List[str]:
        return ["mock"]

    def generate(self, system_prompt, user_prompt, model=None, json_mode=True, timeout=None):
        t0 = time.time()
        # Try to extract agent id from user prompt to vary canned response
        resp = self.canned.get("response")
        if resp is None:
            resp = {
                "current_goal": "Explore and gather resources",
                "reasoning_summary": "Initial exploration to understand surroundings.",
                "plan": ["inspect_environment", "gather_nearby_resources", "report_findings"],
                "priority": "medium",
                "actions": [{"action": "scan_area", "parameters": {"radius": 16}}],
            }
        text = json.dumps(resp)
        return ProviderResponse(text=text, prompt_tokens=10, completion_tokens=20, latency_ms=int((time.time()-t0)*1000), model="mock")
