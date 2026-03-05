import csv
from pathlib import Path

from terminalbench.harness.metrics import Aggregate, EpisodeRecord, aggregate
from terminalbench.tasks.schema import Task


def load_run_csv(path: Path) -> list[EpisodeRecord]:
    records: list[EpisodeRecord] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            records.append(
                EpisodeRecord(
                    task_id=row["task_id"],
                    success=row["success"].lower() == "true",
                    regression=row["regression"].lower() == "true",
                    steps=int(row["steps"]),
                    latency_sec=float(row["latency_sec"]),
                    prompt_tokens=int(row["prompt_tokens"]),
                    completion_tokens=int(row["completion_tokens"]),
                )
            )
    return records


def summarize_split(
    records: list[EpisodeRecord], tasks: list[Task], split: str | None
) -> Aggregate:
    allowed = {task.id for task in tasks if split is None or task.split == split}
    chosen = [row for row in records if row.task_id in allowed]
    return aggregate(chosen)


def by_repo(
    records: list[EpisodeRecord], tasks: list[Task], split: str | None = None
) -> dict[str, Aggregate]:
    task_map = {task.id: task for task in tasks}
    grouped: dict[str, list[EpisodeRecord]] = {}
    for row in records:
        task = task_map.get(row.task_id)
        if task is None:
            continue
        if split is not None and task.split != split:
            continue
        grouped.setdefault(task.repo, []).append(row)
    return {repo: aggregate(rows) for repo, rows in sorted(grouped.items())}
