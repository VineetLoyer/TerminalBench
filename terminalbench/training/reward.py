"""GRPO reward used for the March 2026 QLoRA run.

TRL calls a reward function with the generated completions plus every dataset
column as keyword arguments, so `task_id` arrives alongside each completion.
`SandboxReward` replays the completion's commands in a fresh sandbox, runs the
task grader, and maps the grader flags onto a scalar.
"""

from terminalbench.agent.llm import parse_json
from terminalbench.harness.evaluate import open_sandbox
from terminalbench.tasks.schema import Task

SUCCESS = 1.0
REGRESSION_PENALTY = 0.5
FORMAT_BONUS = 0.1
MAX_COMMANDS = 12


def score_grade(
    success: bool,
    regression: bool,
    well_formed: bool,
    *,
    success_value: float = SUCCESS,
    regression_penalty: float = REGRESSION_PENALTY,
    format_bonus: float = FORMAT_BONUS,
) -> float:
    value = success_value if success else 0.0
    if regression:
        value -= regression_penalty
    if well_formed:
        value += format_bonus
    return value


def completion_text(completion: str | list[dict]) -> str:
    if isinstance(completion, str):
        return completion
    if completion:
        return str(completion[-1].get("content", ""))
    return ""


def extract_commands(text: str) -> list[str]:
    """Commands from `{"commands": [...]}` or a single executor-style `{"command": "..."}`."""
    try:
        payload = parse_json(text)
    except ValueError:
        return []
    commands = payload.get("commands")
    if isinstance(commands, list):
        return [str(item) for item in commands if str(item).strip()][:MAX_COMMANDS]
    command = payload.get("command")
    return [str(command)] if command and str(command).strip() else []


def replay(
    task: Task,
    commands: list[str],
    sandbox: str = "local",
    image_overrides: dict[str, str] | None = None,
) -> dict:
    with open_sandbox(task, sandbox, image_overrides) as box:
        for command in commands:
            box.exec(command, timeout=min(120, task.timeout_sec))
        grade = box.grade(
            task.grader.command,
            task.grader.regression_command,
            task.grader.timeout_sec,
        )
    return {"success": grade.success, "regression": grade.regression}


class SandboxReward:
    """TRL reward function that grades each completion in the task's sandbox."""

    def __init__(
        self,
        tasks: list[Task],
        sandbox: str = "local",
        image_overrides: dict[str, str] | None = None,
        success: float = SUCCESS,
        regression_penalty: float = REGRESSION_PENALTY,
        format_bonus: float = FORMAT_BONUS,
    ):
        self.__name__ = "sandbox_reward"
        self._tasks = {task.id: task for task in tasks}
        self._sandbox = sandbox
        self._image_overrides = image_overrides
        self._weights = {
            "success_value": success,
            "regression_penalty": regression_penalty,
            "format_bonus": format_bonus,
        }

    def __call__(self, completions: list, task_id: list[str], **_: object) -> list[float]:
        scores = []
        for completion, tid in zip(completions, task_id, strict=True):
            commands = extract_commands(completion_text(completion))
            grade = {"success": False, "regression": False}
            if commands:
                grade = replay(self._tasks[tid], commands, self._sandbox, self._image_overrides)
            scores.append(
                score_grade(grade["success"], grade["regression"], bool(commands), **self._weights)
            )
        return scores


def reward(completions: list, grades: list[dict] | None = None, **_: object) -> list[float]:
    """Score completions against grades computed elsewhere."""
    grades = grades or [{} for _ in completions]
    return [
        score_grade(
            bool(grade.get("success")),
            bool(grade.get("regression")),
            bool(extract_commands(completion_text(completion))),
        )
        for completion, grade in zip(completions, grades, strict=True)
    ]
