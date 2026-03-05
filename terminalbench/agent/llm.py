import json
import os
from typing import Protocol

import httpx


class ChatClient(Protocol):
    def complete(self, messages: list[dict], *, role: str) -> str: ...


class OpenAICompatibleClient:
    """Works with vLLM, TGI, or any OpenAI-compatible chat endpoint."""

    def __init__(self, model: str, base_url: str, api_key: str, timeout: float = 120):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def complete(self, messages: list[dict], *, role: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "temperature": 0.2},
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        usage = body.get("usage") or {}
        self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
        self.completion_tokens += int(usage.get("completion_tokens") or 0)
        return body["choices"][0]["message"]["content"]


class ScriptedClient:
    """Test double. Each complete() call pops the next canned string."""

    def __init__(self, replies: list[str]):
        self._replies = list(replies)
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def complete(self, messages: list[dict], *, role: str) -> str:
        if not self._replies:
            raise RuntimeError(f"scripted client ran out of replies at role={role}")
        text = self._replies.pop(0)
        self.prompt_tokens += 32
        self.completion_tokens += max(8, len(text) // 4)
        return text


def client_from_env() -> ChatClient:
    model = os.environ.get("TERMINALBENCH_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct")
    base_url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "local")
    return OpenAICompatibleClient(model=model, base_url=base_url, api_key=api_key)


def parse_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model reply did not contain a JSON object")
    return json.loads(text[start : end + 1])
