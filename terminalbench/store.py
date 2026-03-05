import json
import os
from typing import Protocol


class RunStore(Protocol):
    def put_run(self, run_id: str, payload: dict) -> None: ...
    def get_run(self, run_id: str) -> dict | None: ...
    def list_runs(self) -> list[str]: ...


class MemoryStore:
    def __init__(self):
        self._runs: dict[str, dict] = {}

    def put_run(self, run_id: str, payload: dict) -> None:
        self._runs[run_id] = payload

    def get_run(self, run_id: str) -> dict | None:
        return self._runs.get(run_id)

    def list_runs(self) -> list[str]:
        return sorted(self._runs)


class RedisStore:
    def __init__(self, url: str):
        import redis

        self._redis = redis.Redis.from_url(url, decode_responses=True)
        self._redis.ping()

    def put_run(self, run_id: str, payload: dict) -> None:
        self._redis.hset("terminalbench:runs", run_id, json.dumps(payload))

    def get_run(self, run_id: str) -> dict | None:
        raw = self._redis.hget("terminalbench:runs", run_id)
        return json.loads(raw) if raw else None

    def list_runs(self) -> list[str]:
        return sorted(self._redis.hkeys("terminalbench:runs"))


def open_store() -> RunStore:
    url = os.environ.get("TERMINALBENCH_REDIS_URL", "")
    if not url:
        return MemoryStore()
    try:
        return RedisStore(url)
    except Exception:  # noqa: BLE001 — any Redis failure falls back to memory
        # Redis is optional. A refused connection should not take the API down.
        return MemoryStore()
