from pathlib import Path

from terminalbench.tasks.loader import load_tasks
from terminalbench.training.grpo import prepare


def test_dry_run_writes_train_prompts(tmp_path: Path):
    summary = prepare(Path("configs/train.yaml"), load_tasks(), tmp_path)
    assert summary["n_prompts"] == 25
    assert summary["base_model"] == "Qwen/Qwen2.5-3B-Instruct"
    lines = (tmp_path / "train.jsonl").read_text().strip().splitlines()
    assert len(lines) == 25
