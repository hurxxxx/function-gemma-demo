#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoProcessor, Trainer, TrainingArguments

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.append(str(BACKEND_DIR))

from home_controller import HOME_FUNCTION_SCHEMAS  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FunctionGemma LoRA fine-tuning")
    parser.add_argument("--model_id", default="google/functiongemma-270m-it")
    parser.add_argument("--train_file", required=True)
    parser.add_argument("--eval_file", default=None)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--max_seq_length", type=int, default=1024)
    parser.add_argument("--num_train_epochs", type=int, default=3)
    parser.add_argument("--per_device_train_batch_size", type=int, default=2)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=2)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=1e-4)
    parser.add_argument("--logging_steps", type=int, default=20)
    parser.add_argument("--save_steps", type=int, default=200)
    parser.add_argument("--save_total_limit", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gradient_checkpointing", action="store_true")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument(
        "--attn_implementation",
        default="eager",
        choices=["eager", "sdpa", "flash_attention_2"],
    )
    return parser.parse_args()


def _select_dtype(args: argparse.Namespace) -> torch.dtype:
    if args.bf16:
        return torch.bfloat16
    if args.fp16:
        return torch.float16
    return torch.float32


def _truncate(example: Dict[str, List[int]], max_len: int) -> Dict[str, List[int]]:
    if max_len <= 0:
        return example
    if len(example["input_ids"]) <= max_len:
        return example
    return {
        "input_ids": example["input_ids"][-max_len:],
        "attention_mask": example["attention_mask"][-max_len:],
        "labels": example["labels"][-max_len:],
    }


def _build_sample(
    processor: AutoProcessor,
    messages: List[Dict[str, str]],
    max_len: int,
) -> Dict[str, List[int]]:
    if not messages or messages[-1].get("role") != "assistant":
        raise ValueError("Each sample must end with an assistant tool-call message.")

    prompt_messages = messages[:-1]

    prompt_inputs = processor.apply_chat_template(
        prompt_messages,
        tools=HOME_FUNCTION_SCHEMAS,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    full_inputs = processor.apply_chat_template(
        messages,
        tools=HOME_FUNCTION_SCHEMAS,
        add_generation_prompt=False,
        return_dict=True,
        return_tensors="pt",
    )

    input_ids = full_inputs["input_ids"][0]
    attention_mask = full_inputs.get("attention_mask")
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids)
    else:
        attention_mask = attention_mask[0]

    labels = input_ids.clone()
    prompt_len = prompt_inputs["input_ids"].shape[1]
    labels[:prompt_len] = -100

    example = {
        "input_ids": input_ids.tolist(),
        "attention_mask": attention_mask.tolist(),
        "labels": labels.tolist(),
    }
    return _truncate(example, max_len)


@dataclass
class CausalLMDataCollator:
    tokenizer: Any
    pad_to_multiple_of: int | None = 8

    def __call__(self, features: List[Dict[str, List[int]]]) -> Dict[str, torch.Tensor]:
        input_ids = [f["input_ids"] for f in features]
        attention_mask = [f["attention_mask"] for f in features]
        labels = [f["labels"] for f in features]

        batch = self.tokenizer.pad(
            {"input_ids": input_ids, "attention_mask": attention_mask},
            padding=True,
            return_tensors="pt",
            pad_to_multiple_of=self.pad_to_multiple_of,
        )
        labels_batch = self.tokenizer.pad(
            {"input_ids": labels},
            padding=True,
            return_tensors="pt",
            pad_to_multiple_of=self.pad_to_multiple_of,
        )["input_ids"]

        labels_batch[labels_batch == self.tokenizer.pad_token_id] = -100
        batch["labels"] = labels_batch
        return batch


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)

    processor = AutoProcessor.from_pretrained(args.model_id, trust_remote_code=True)
    tokenizer = getattr(processor, "tokenizer", processor)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    dtype = _select_dtype(args)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=dtype,
        attn_implementation=args.attn_implementation,
        trust_remote_code=True,
    )

    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    dataset = load_dataset("json", data_files=args.train_file)["train"]

    def tokenize_fn(example: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[int]]:
        messages = example.get("messages")
        if not isinstance(messages, list):
            raise ValueError("Each sample must contain a 'messages' list.")
        return _build_sample(processor, messages, args.max_seq_length)

    dataset = dataset.map(tokenize_fn, remove_columns=dataset.column_names)

    eval_dataset = None
    if args.eval_file:
        eval_dataset = load_dataset("json", data_files=args.eval_file)["train"]
        eval_dataset = eval_dataset.map(tokenize_fn, remove_columns=eval_dataset.column_names)

    data_collator = CausalLMDataCollator(tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        num_train_epochs=args.num_train_epochs,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        eval_strategy="steps" if eval_dataset is not None else "no",
        eval_steps=args.save_steps if eval_dataset is not None else None,
        fp16=args.fp16,
        bf16=args.bf16,
        seed=args.seed,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    trainer.train()
    model.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()
