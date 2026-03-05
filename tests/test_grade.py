from terminalbench.harness.runner import grade_workspace, run_scripted
from terminalbench.tasks.loader import load_tasks


def _task(task_id):
    return next(task for task in load_tasks() if task.id == task_id)


def test_buggy_fixture_fails_and_solution_passes():
    for task_id in [
        "click-default-envvar",
        "rich-table-width",
        "httpie-bool-json",
        "rg-glob-negation",
        "fd-hidden-flag",
    ]:
        buggy = grade_workspace(_task(task_id), use_solution=False)
        fixed = grade_workspace(_task(task_id), use_solution=True)
        assert buggy["success"] is False, task_id
        assert fixed["success"] is True, fixed
        assert fixed["regression"] is False


def test_scripted_episode_submits_after_one_command():
    replies = [
        '{"steps": ["list files", "run public tests"], "notes": ""}',
        '{"command": "python -m pytest tests/test_public.py -q", "rationale": "baseline"}',
        '{"decision": "submit", "notes": "public tests are the visible signal"}',
    ]
    record = run_scripted(_task("click-default-envvar"), replies)
    assert record["steps"] == 1
    assert record["success"] is False
    assert record["prompt_tokens"] > 0
