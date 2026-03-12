import json

import pytest

from terminalbench.paths import FIXTURES_DIR
from terminalbench.tasks.loader import load_tasks
from terminalbench.training.reward import SandboxReward, extract_commands, reward, score_grade


def test_extract_commands():
    assert extract_commands('{"commands": ["ls", " ", "pytest"]}') == ["ls", "pytest"]
    assert extract_commands('sure: {"command": "ls"}') == ["ls"]
    assert extract_commands("no json here") == []
    assert extract_commands('{"commands": []}') == []


def test_score_grade():
    assert score_grade(True, False, True) == pytest.approx(1.1)
    assert score_grade(False, True, True) == pytest.approx(-0.4)
    assert score_grade(False, False, False) == 0.0


def test_precomputed_reward_accepts_chat_completions():
    completions = [[{"role": "assistant", "content": '{"command": "ls"}'}], "garbage"]
    grades = [{"success": True}, {}]
    assert reward(completions, grades=grades) == pytest.approx([1.1, 0.0])


def test_sandbox_reward_grades_each_completion():
    solution = (FIXTURES_DIR / "click-default-envvar" / "solution" / "app.py").as_posix()
    fix = f"python -c \"import shutil; shutil.copy(r'{solution}', 'app.py')\""
    completions = [
        json.dumps({"commands": [fix]}),
        json.dumps({"commands": ["python -m pytest tests/test_public.py -q"]}),
        "I would edit app.py",
    ]
    score = SandboxReward(load_tasks())
    assert score.__name__ == "sandbox_reward"
    values = score(completions, task_id=["click-default-envvar"] * 3)
    assert values == pytest.approx([1.1, 0.1, 0.0])
