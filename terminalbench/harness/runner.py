from pathlib import Path

from terminalbench.agent.llm import ScriptedClient
from terminalbench.agent.loop import EpisodeRunner, apply_oracle
from terminalbench.paths import FIXTURES_DIR
from terminalbench.sandbox.local import LocalSandbox
from terminalbench.tasks.schema import Task


def fixture_root(task: Task) -> Path:
    if not task.fixture:
        raise ValueError(f"{task.id} has no local fixture")
    root = FIXTURES_DIR / task.fixture
    if not (root / "workspace").is_dir():
        raise FileNotFoundError(root)
    return root


def grade_workspace(task: Task, use_solution: bool) -> dict:
    root = fixture_root(task)
    sandbox = LocalSandbox(root / "workspace", hidden=root / "hidden")
    try:
        if use_solution:
            apply_oracle(sandbox, root / "solution")
        grade = sandbox.grade(
            task.grader.command,
            task.grader.regression_command,
            task.grader.timeout_sec,
        )
        return {
            "task_id": task.id,
            "success": grade.success,
            "regression": grade.regression,
            "exit_code": grade.target.exit_code,
            "stdout": grade.target.stdout,
            "stderr": grade.target.stderr,
        }
    finally:
        sandbox.close()


def run_scripted(task: Task, replies: list[str]) -> dict:
    root = fixture_root(task)
    sandbox = LocalSandbox(root / "workspace", hidden=root / "hidden")
    try:
        trajectory = EpisodeRunner(ScriptedClient(replies), max_steps=4).run(task, sandbox)
        record = trajectory.to_record()
        return record.model_dump()
    finally:
        sandbox.close()
