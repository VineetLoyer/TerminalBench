import json
from pathlib import Path

from terminalbench.tasks.schema import Task


def build_prompts(tasks: list[Task], split: str = "train") -> list[dict]:
    rows = []
    for task in tasks:
        if task.split != split:
            continue
        rows.append(
            {
                "task_id": task.id,
                "repo": task.repo,
                "prompt": (
                    "You are a terminal coding agent with planner, executor, and reviewer roles. "
                    "Solve the task inside the sandbox. Preserve existing behavior.\n\n"
                    f"Repository: {task.repo}\n"
                    f"Task: {task.title}\n\n"
                    f"{task.instruction.strip()}\n\n"
                    "Reply with JSON only: "
                    '{"commands": ["...", "..."]}. '
                    "Commands run in order from the repository root.\n"
                ),
            }
        )
    return rows


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
