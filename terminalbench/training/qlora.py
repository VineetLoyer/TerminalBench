"""QLoRA adapter setup for a 3B instruct model.

Imports of transformers/peft are deferred so the rest of the platform runs
without a GPU stack. `terminalbench train --dry-run` never touches them.
"""

from pathlib import Path

import yaml


def load_train_config(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text())
    required = ["base_model", "lora", "grpo"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"train config missing {missing}")
    return payload


def build_model_and_tokenizer(cfg: dict):
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=cfg["lora"].get("bnb_4bit_quant_type", "nf4"),
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(cfg["base_model"], use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        cfg["base_model"],
        quantization_config=quant,
        device_map="auto",
    )
    model = prepare_model_for_kbit_training(model)
    lora = LoraConfig(
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["alpha"],
        lora_dropout=cfg["lora"].get("dropout", 0.05),
        target_modules=cfg["lora"]["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    return get_peft_model(model, lora), tokenizer
