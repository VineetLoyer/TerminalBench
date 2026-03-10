"""Live evaluation: run the agent on bank tasks and write an episode ledger."""

import shutil
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx
import yaml

from terminalbench.agent.llm import ChatClient
from terminalbench.agent.loop import EpisodeRunner, trajectory_json
from terminalbench.harness.metrics import EpisodeRecord
from terminalbench.harness.report import write_run_csv
from terminalbench.paths import FIXTURES_DIR
from terminalbench.sandbox.base import Sandbox
from terminalbench.sandbox.docker import DockerSandbox
from terminalbench.sandbox.local import LocalSandbox, remove_tree
from terminalbench.tasks.checkout import checkout
from terminalbench.tasks.schema import Task

SANDBOXES = ("local", "docker")


def load_eval_config(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text()) or {}
    payload.setdefault("sandbox", "local")
    payload.setdefault("max_steps", 12)
    payload.setdefault("splits", ["train", "held_out"])
    payload.setdefault("image_overrides", {})
    if payload["sandbox"] not in SANDBOXES:
        raise ValueError(f"sandbox must be one of {SANDBOXES}, got {payload['sandbox']!r}")
    return payload


def select_tasks(
    tasks: list[Task],
    task_ids: list[str] | None = None,
    splits: list[str] | None = None,
    fixtures_only: bool = False,
) -> list[Task]:
    if task_ids:
        index = {task.id: task for task in tasks}
        unknown = [task_id for task_id in task_ids if task_id not in index]
        if unknown:
            raise KeyError(f"unknown task ids: {', '.join(unknown)}")
        chosen = [index[task_id] for task_id in task_ids]
    else:
        chosen = [task for task in tasks if not splits or task.split in splits]
    if fixtures_only:
        chosen = [task for task in chosen if task.fixture]
    return chosen


@contextmanager
def open_sandbox(
    task: Task, kind: str = "local", image_overrides: dict[str, str] | None = None
) -> Iterator[Sandbox]:
    """Fresh sandbox for one episode: the fixture workspace, or an upstream checkout."""
    if kind not in SANDBOXES:
        raise ValueError(f"sandbox must be one of {SANDBOXES}, got {kind!r}")
    scratch = Path(tempfile.mkdtemp(prefix="tb-ws-"))
    hidden = None
    try:
        if task.fixture:
            root = FIXTURES_DIR / task.fixture
            source = root / "workspace"
            hidden = root / "hidden"
        else:
            source = checkout(task, scratch / "repo")
        if kind == "docker":
            # The container bind-mounts its workdir, so never hand it the fixture itself.
            work = source
            if task.fixture:
                work = scratch / "work"
                shutil.copytree(source, work)
            image = (image_overrides or {}).get(task.image, task.image)
            sandbox: Sandbox = DockerSandbox(work, image=image, hidden=hidden)
        else:
            sandbox = LocalSandbox(source, hidden=hidden)
        try:
            yield sandbox
        finally:
            sandbox.close()
    finally:
        remove_tree(scratch)


def run_suite(
    tasks: list[Task],
    client_factory: Callable[[], ChatClient],
    out_dir: Path,
    *,
    sandbox: str = "local",
    max_steps: int = 12,
    image_overrides: dict[str, str] | None = None,
    log: Callable[[str], None] = print,
) -> list[EpisodeRecord]:
    """Run one episode per task, writing trajectories and `<out_dir.name>.csv` as it goes."""
    traj_dir = out_dir / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)
    ledger = out_dir / f"{out_dir.name}.csv"
    records: list[EpisodeRecord] = []
    for index, task in enumerate(tasks, start=1):
        client = client_factory()
        started = time.monotonic()
        with open_sandbox(task, sandbox, image_overrides) as box:
            try:
                trajectory = EpisodeRunner(client, max_steps=max_steps).run(task, box)
            except httpx.ConnectError:
                raise
            except Exception as exc:  # noqa: BLE001 — one bad episode should not end the run
                (traj_dir / f"{task.id}.error.txt").write_text(f"{type(exc).__name__}: {exc}\n")
                record = EpisodeRecord(
                    task_id=task.id,
                    success=False,
                    regression=False,
                    steps=0,
                    latency_sec=time.monotonic() - started,
                    prompt_tokens=getattr(client, "prompt_tokens", 0),
                    completion_tokens=getattr(client, "completion_tokens", 0),
                )
                status = f"error ({type(exc).__name__})"
            else:
                (traj_dir / f"{task.id}.json").write_text(trajectory_json(trajectory))
                record = trajectory.to_record()
                status = "pass" if record.success else ("regression" if record.regression else "fail")
        records.append(record)
        write_run_csv(ledger, records)
        log(f"[{index}/{len(tasks)}] {task.id}: {status} in {record.latency_sec:.1f}s")
    return records
