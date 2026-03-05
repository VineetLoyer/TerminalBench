from pathlib import Path

import yaml

from terminalbench.paths import BANK_DIR
from terminalbench.tasks.schema import Task


def load_tasks(bank_dir: Path | None = None) -> list[Task]:
    directory = bank_dir or BANK_DIR
    tasks: list[Task] = []
    for path in sorted(directory.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text()) or {}
        for item in payload.get("tasks", []):
            tasks.append(Task.model_validate(item))
    ids = [task.id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task id in bank")
    return tasks


def by_id(tasks: list[Task]) -> dict[str, Task]:
    return {task.id: task for task in tasks}
