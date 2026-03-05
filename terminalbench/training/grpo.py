"""GRPO fine-tune on the train split.

The reward function is `terminalbench.training.reward.reward`. Completions are
graded by replaying the executor command in the sandbox harness. This module
only wires TRL; it does not download weights on import.
"""

from pathlib import Path

from terminalbench.training.dataset import build_prompts, write_jsonl
from terminalbench.training.qlora import load_train_config


def prepare(cfg_path: Path, tasks, out_dir: Path) -> dict:
    cfg = load_train_config(cfg_path)
    rows = build_prompts(tasks, split="train")
    write_jsonl(rows, out_dir / "train.jsonl")
    summary = {
        "base_model": cfg["base_model"],
        "method": cfg.get("method", "qlora+grpo"),
        "n_prompts": len(rows),
        "lora_r": cfg["lora"]["r"],
        "lora_alpha": cfg["lora"]["alpha"],
        "grpo_beta": cfg["grpo"]["beta"],
        "num_generations": cfg["grpo"]["num_generations"],
        "max_steps": cfg["grpo"].get("max_steps"),
        "dataset": str(out_dir / "train.jsonl"),
    }
    (out_dir / "prepare.json").write_text(__import__("json").dumps(summary, indent=2))
    return summary


def train(cfg_path: Path, dataset_path: Path, output_dir: Path) -> None:
    from datasets import load_dataset
    from trl import GRPOConfig, GRPOTrainer

    from terminalbench.training.qlora import build_model_and_tokenizer
    from terminalbench.training.reward import reward

    cfg = load_train_config(cfg_path)
    model, tokenizer = build_model_and_tokenizer(cfg)
    dataset = load_dataset("json", data_files=str(dataset_path), split="train")
    grpo = cfg["grpo"]
    args = GRPOConfig(
        output_dir=str(output_dir),
        learning_rate=grpo.get("learning_rate", 5e-6),
        per_device_train_batch_size=grpo.get("per_device_train_batch_size", 1),
        gradient_accumulation_steps=grpo.get("gradient_accumulation_steps", 8),
        max_steps=grpo.get("max_steps", 400),
        num_generations=grpo["num_generations"],
        beta=grpo["beta"],
        max_completion_length=grpo.get("max_completion_length", 1024),
        logging_steps=10,
        save_steps=100,
        bf16=True,
        report_to=[],
    )
    trainer = GRPOTrainer(
        model=model,
        reward_funcs=reward,
        args=args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(output_dir / "adapter"))
