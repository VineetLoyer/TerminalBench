from pathlib import Path

import pytest

from terminalbench.agent.llm import ScriptedClient
from terminalbench.harness.evaluate import load_eval_config, run_suite, select_tasks
from terminalbench.harness.report import load_run_csv
from terminalbench.tasks.loader import load_tasks

SUBMIT_AFTER_ONE = [
    '{"steps": ["run public tests"], "notes": ""}',
    '{"command": "python -m pytest tests/test_public.py -q", "rationale": "baseline"}',
    '{"decision": "submit", "notes": ""}',
]


def test_eval_config_defaults():
    cfg = load_eval_config(Path("configs/eval.yaml"))
    assert cfg["sandbox"] == "local"
    assert cfg["max_steps"] == 12
    assert cfg["image_overrides"]["python:3.12-slim"] == "terminalbench-sandbox"


def test_select_tasks():
    tasks = load_tasks()
    assert len(select_tasks(tasks, splits=["held_out"])) == 35
    assert len(select_tasks(tasks, fixtures_only=True)) == 5
    assert [t.id for t in select_tasks(tasks, ["fd-hidden-flag"])] == ["fd-hidden-flag"]
    with pytest.raises(KeyError):
        select_tasks(tasks, ["nope"])


def test_run_suite_writes_ledger_and_survives_a_bad_episode(tmp_path: Path):
    tasks = select_tasks(load_tasks(), ["click-default-envvar", "fd-hidden-flag"])
    replies = iter([SUBMIT_AFTER_ONE, ["not json at all"]])
    out = tmp_path / "smoke"
    records = run_suite(tasks, lambda: ScriptedClient(next(replies)), out, log=lambda _: None)

    assert [r.task_id for r in records] == ["click-default-envvar", "fd-hidden-flag"]
    assert records[0].steps == 1 and records[0].success is False
    assert records[1].steps == 0 and records[1].success is False
    assert (out / "trajectories" / "click-default-envvar.json").is_file()
    assert (out / "trajectories" / "fd-hidden-flag.error.txt").is_file()
    assert [r.task_id for r in load_run_csv(out / "smoke.csv")] == [r.task_id for r in records]
