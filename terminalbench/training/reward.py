"""GRPO reward used for the March 2026 QLoRA run.

The trainer calls `reward(completions, task_ids=...)` after a generation group.
Scoring itself happens in the sandbox; this function only maps grader flags
onto a scalar so TRL can consume it.
"""

SUCCESS = 1.0
REGRESSION_PENALTY = 0.5
FORMAT_BONUS = 0.1


def score_grade(success: bool, regression: bool, well_formed: bool) -> float:
    value = SUCCESS if success else 0.0
    if regression:
        value -= REGRESSION_PENALTY
    if well_formed:
        value += FORMAT_BONUS
    return value


def reward(completions: list[str], grades: list[dict] | None = None, **_: object) -> list[float]:
    grades = grades or [{} for _ in completions]
    scores = []
    for text, grade in zip(completions, grades, strict=True):
        well_formed = '"command"' in text or text.strip().startswith("{")
        scores.append(
            score_grade(
                bool(grade.get("success")),
                bool(grade.get("regression")),
                well_formed,
            )
        )
    return scores
