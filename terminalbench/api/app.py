from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from terminalbench import __version__
from terminalbench.harness.metrics import EpisodeRecord
from terminalbench.harness.report import by_repo, load_run_csv, summarize_split
from terminalbench.paths import CONFIGS_DIR, RESULTS_DIR
from terminalbench.store import open_store
from terminalbench.tasks.loader import load_tasks
from terminalbench.training.qlora import load_train_config

app = FastAPI(title="TerminalBench", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TASKS = load_tasks()
TASK_INDEX = {task.id: task for task in TASKS}
STORE = open_store()


def _run_paths() -> list[Path]:
    return sorted(RESULTS_DIR.glob("*.csv"))


def _run_payload(path: Path) -> dict:
    records = load_run_csv(path)
    cached = STORE.get_run(path.stem)
    if cached:
        return cached
    payload = _build_payload(path, records)
    STORE.put_run(path.stem, payload)
    return payload


def _build_payload(path: Path, records: list[EpisodeRecord]) -> dict:
    meta = {
        "2026-02-24-baseline": {
            "label": "Qwen2.5-3B-Instruct",
            "kind": "baseline",
            "date": "2026-02-24",
            "notes": "Unadapted 3B instruct model. Same sandbox, grader, and step budget as the tuned run.",
        },
        "2026-03-03-qlora-grpo": {
            "label": "Qwen2.5-3B + QLoRA/GRPO",
            "kind": "tuned",
            "date": "2026-03-03",
            "notes": "4-bit QLoRA adapter trained with GRPO on the 25-task train split.",
        },
    }.get(path.stem, {"label": path.stem, "kind": "custom", "date": "", "notes": ""})
    return {
        "id": path.stem,
        **meta,
        "overall": summarize_split(records, TASKS, None).as_dict(),
        "train": summarize_split(records, TASKS, "train").as_dict(),
        "held_out": summarize_split(records, TASKS, "held_out").as_dict(),
        "by_repo": {repo: agg.as_dict() for repo, agg in by_repo(records, TASKS).items()},
        "held_out_by_repo": {
            repo: agg.as_dict() for repo, agg in by_repo(records, TASKS, split="held_out").items()
        },
        "episodes": [
            {
                **record.model_dump(),
                "cost_usd": round(record.cost_usd(), 4),
                "repo": TASK_INDEX[record.task_id].repo,
                "title": TASK_INDEX[record.task_id].title,
                "split": TASK_INDEX[record.task_id].split,
                "difficulty": TASK_INDEX[record.task_id].difficulty,
            }
            for record in records
            if record.task_id in TASK_INDEX
        ],
    }


@app.get("/health")
def health():
    return {"ok": True, "version": __version__, "tasks": len(TASKS)}


@app.get("/tasks")
def list_tasks(repo: str | None = None, split: str | None = None):
    rows = []
    for task in TASKS:
        if repo and task.repo != repo:
            continue
        if split and task.split != split:
            continue
        rows.append(task.model_dump())
    return {"tasks": rows, "count": len(rows)}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = TASK_INDEX.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="unknown task")
    return task.model_dump()


@app.get("/repos")
def repos():
    counts: dict[str, dict] = {}
    for task in TASKS:
        bucket = counts.setdefault(task.repo, {"repo": task.repo, "tasks": 0, "train": 0, "held_out": 0})
        bucket["tasks"] += 1
        bucket[task.split] += 1
    return {"repos": list(counts.values())}


@app.get("/runs")
def list_runs():
    runs = []
    for path in _run_paths():
        payload = _run_payload(path)
        runs.append(
            {
                "id": payload["id"],
                "label": payload["label"],
                "kind": payload["kind"],
                "date": payload["date"],
                "notes": payload["notes"],
                "overall": payload["overall"],
                "held_out": payload["held_out"],
            }
        )
    return {"runs": runs}


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    path = RESULTS_DIR / f"{run_id}.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="unknown run")
    return _run_payload(path)


@app.get("/compare")
def compare():
    baseline = _run_payload(RESULTS_DIR / "2026-02-24-baseline.csv")
    tuned = _run_payload(RESULTS_DIR / "2026-03-03-qlora-grpo.csv")
    return {"baseline": baseline, "tuned": tuned}


@app.get("/training")
def training():
    cfg = load_train_config(CONFIGS_DIR / "train.yaml")
    curve_path = RESULTS_DIR / "reward_curve.json"
    curve = []
    if curve_path.exists():
        import json

        curve = json.loads(curve_path.read_text())
    return {"config": cfg, "reward_curve": curve}
