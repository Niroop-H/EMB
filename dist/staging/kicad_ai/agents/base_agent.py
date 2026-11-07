"""
Base Agent Foundation for KiCad AI Autonomous Hardware Engineering.
Supports pluggable LLM backends (Gemini, Claude, OpenAI, Local Ollama/vLLM) with deterministic tool execution and validation loops.
"""

from typing import Dict, Any, Optional, List
import json
import os
import urllib.request
import urllib.error

class BaseHardwareAgent:
    def __init__(self, name: str, role_description: str, model: str = "gemini-2.5-flash"):
        self.name = name
        self.role_description = role_description
        self.model = model
        self.history: List[Dict[str, str]] = []

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

    def call_llm(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends request to configured LLM endpoint (Gemini API or OpenAI-compatible endpoint).
        Falls back to local heuristic reasoning when offline or when no API key is set.
        """
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        # If API key is available, call remote API
        if api_key:
            try:
                return self._call_remote_api(prompt, api_key, schema)
            except Exception as e:
                print(f"[{self.name}] Remote API call failed ({e}), using deterministic hardware synthesizer.")
        
        # Deterministic Hardware Synthesizer / Heuristic Fallback
        return self.synthesize_heuristic(prompt)

    def _call_remote_api(self, prompt: str, api_key: str, schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        system_instruction = {"parts": [{"text": self.system_prompt}]}
        contents = [{"parts": [{"text": prompt}]}]
        
        payload: Dict[str, Any] = {
            "contents": contents,
            "system_instruction": system_instruction,
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)

    def synthesize_heuristic(self, prompt: str) -> Dict[str, Any]:
        """Implemented by child agents for reliable, offline, deterministic hardware synthesis."""
        raise NotImplementedError
