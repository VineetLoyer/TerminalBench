import json
import time
from dataclasses import dataclass, field

from terminalbench.agent.llm import ChatClient, parse_json
from terminalbench.agent.prompts import (
    EXECUTOR_SYSTEM,
    PLANNER_SYSTEM,
    REVIEWER_SYSTEM,
    executor_user,
    planner_user,
    reviewer_user,
)
from terminalbench.harness.metrics import EpisodeRecord
from terminalbench.sandbox.base import Sandbox
from terminalbench.tasks.schema import Task


@dataclass
class StepLog:
    role: str
    content: str


@dataclass
class Trajectory:
    task_id: str
    steps: list[StepLog] = field(default_factory=list)
    grade_success: bool = False
    grade_regression: bool = False
    latency_sec: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def to_record(self) -> EpisodeRecord:
        actions = [step for step in self.steps if step.role == "executor"]
        return EpisodeRecord(
            task_id=self.task_id,
            success=self.grade_success,
            regression=self.grade_regression,
            steps=len(actions),
            latency_sec=self.latency_sec,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
        )


class EpisodeRunner:
    def __init__(self, client: ChatClient, max_steps: int = 12):
        self.client = client
        self.max_steps = max_steps

    def run(self, task: Task, sandbox: Sandbox) -> Trajectory:
        started = time.monotonic()
        trajectory = Trajectory(task_id=task.id)
        listing = sandbox.exec("ls -la").stdout
        plan = self._plan(task, listing, None, trajectory)
        transcript = ""
        for _ in range(self.max_steps):
            action = self._act(task, plan, transcript, trajectory)
            command = str(action.get("command") or "true")
            result = sandbox.exec(command, timeout=min(120, task.timeout_sec))
            blob = f"$ {command}\n{result.stdout}\n{result.stderr}"
            transcript = (transcript + "\n" + blob)[-6000:]
            trajectory.steps.append(StepLog("sandbox", blob[:2000]))
            review = self._review(task, command, blob, trajectory)
            decision = review.get("decision", "continue")
            if decision == "submit":
                break
            if decision == "replan":
                plan = self._plan(task, listing, review.get("notes"), trajectory)
        grade = sandbox.grade(
            task.grader.command,
            task.grader.regression_command,
            task.grader.timeout_sec,
        )
        trajectory.grade_success = grade.success
        trajectory.grade_regression = grade.regression
        trajectory.latency_sec = time.monotonic() - started
        trajectory.prompt_tokens = getattr(self.client, "prompt_tokens", 0)
        trajectory.completion_tokens = getattr(self.client, "completion_tokens", 0)
        return trajectory

    def _plan(self, task, listing, feedback, trajectory) -> list[str]:
        raw = self.client.complete(
            [
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user", "content": planner_user(task.instruction, listing, feedback)},
            ],
            role="planner",
        )
        trajectory.steps.append(StepLog("planner", raw))
        parsed = parse_json(raw)
        steps = parsed.get("steps") or []
        return [str(step) for step in steps]

    def _act(self, task, plan, transcript, trajectory) -> dict:
        raw = self.client.complete(
            [
                {"role": "system", "content": EXECUTOR_SYSTEM},
                {"role": "user", "content": executor_user(task.instruction, plan, transcript)},
            ],
            role="executor",
        )
        trajectory.steps.append(StepLog("executor", raw))
        return parse_json(raw)

    def _review(self, task, command, output, trajectory) -> dict:
        raw = self.client.complete(
            [
                {"role": "system", "content": REVIEWER_SYSTEM},
                {"role": "user", "content": reviewer_user(task.instruction, command, output)},
            ],
            role="reviewer",
        )
        trajectory.steps.append(StepLog("reviewer", raw))
        return parse_json(raw)


def apply_oracle(sandbox: Sandbox, solution_dir) -> None:
    """Copy the reference fix into the workspace. Used to validate graders, not as a model."""
    import shutil

    for path in solution_dir.rglob("*"):
        if path.is_file():
            dest = sandbox.workdir / path.relative_to(solution_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, dest)


def trajectory_json(trajectory: Trajectory) -> str:
    return json.dumps(
        {
            "task_id": trajectory.task_id,
            "success": trajectory.grade_success,
            "steps": [step.__dict__ for step in trajectory.steps],
        },
        indent=2,
    )
