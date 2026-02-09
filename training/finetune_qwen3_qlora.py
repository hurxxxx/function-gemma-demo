#!/usr/bin/env python3
"""
Qwen3-30B-A3B QLoRA 파인튜닝 스크립트
ROCm gfx1151 (Ryzen AI Max+ 395) 환경
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# ROCm 환경 변수 설정
os.environ["HSA_ENABLE_SDMA"] = "0"
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen3 QLoRA fine-tuning")
    parser.add_argument("--model_id", default="Qwen/Qwen3-30B-A3B")
    parser.add_argument("--train_file", required=True)
    parser.add_argument("--eval_file", default=None)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--max_seq_length", type=int, default=512)
    parser.add_argument("--num_train_epochs", type=int, default=1)
    parser.add_argument("--per_device_train_batch_size", type=int, default=1)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=1)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=16)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--logging_steps", type=int, default=10)
    parser.add_argument("--save_steps", type=int, default=100)
    parser.add_argument("--save_total_limit", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gradient_checkpointing", action="store_true", default=True)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--max_samples", type=int, default=None, help="테스트용: 최대 샘플 수")
    return parser.parse_args()


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
    tokenizer: AutoTokenizer,
    messages: List[Dict[str, str]],
    max_len: int,
) -> Dict[str, List[int]]:
    """메시지를 토크나이즈하고 라벨 마스킹 적용"""
    if not messages or messages[-1].get("role") != "assistant":
        raise ValueError("Each sample must end with an assistant message.")

    # 프롬프트 (assistant 응답 전까지)
    prompt_messages = messages[:-1]

    # 프롬프트만 토크나이즈
    prompt_text = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    prompt_ids = tokenizer(prompt_text, return_tensors="pt")["input_ids"][0]

    # 전체 대화 토크나이즈
    full_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    full_ids = tokenizer(full_text, return_tensors="pt")["input_ids"][0]

    # 라벨: 프롬프트 부분은 -100으로 마스킹
    labels = full_ids.clone()
    prompt_len = len(prompt_ids)
    labels[:prompt_len] = -100

    example = {
        "input_ids": full_ids.tolist(),
        "attention_mask": [1] * len(full_ids),
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

    print("=" * 60)
    print("Qwen3 QLoRA Fine-tuning")
    print("=" * 60)
    print(f"Model: {args.model_id}")
    print(f"Train file: {args.train_file}")
    print(f"Output dir: {args.output_dir}")
    print(f"Max seq length: {args.max_seq_length}")
    print(f"LoRA r={args.lora_r}, alpha={args.lora_alpha}")

    # 4bit 양자화 설정
    print("\n[1/5] BitsAndBytesConfig 설정...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # 토크나이저 로드
    print("\n[2/5] 토크나이저 로드...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # 모델 로드
    print("\n[3/5] 모델 로드 (4bit 양자화)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="eager",  # gfx1151 필수
    )

    # QLoRA 준비
    print("\n[4/5] QLoRA 설정...")
    model = prepare_model_for_kbit_training(model)

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
    model.print_trainable_parameters()

    # 데이터셋 로드
    print("\n[5/5] 데이터셋 로드 및 전처리...")
    dataset = load_dataset("json", data_files=args.train_file)["train"]

    if args.max_samples:
        dataset = dataset.select(range(min(args.max_samples, len(dataset))))
        print(f"  테스트 모드: {len(dataset)} 샘플만 사용")

    def tokenize_fn(example: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[int]]:
        messages = example.get("messages")
        if not isinstance(messages, list):
            raise ValueError("Each sample must contain a 'messages' list.")
        return _build_sample(tokenizer, messages, args.max_seq_length)

    dataset = dataset.map(tokenize_fn, remove_columns=dataset.column_names)
    print(f"  학습 샘플: {len(dataset)}")

    eval_dataset = None
    if args.eval_file:
        eval_dataset = load_dataset("json", data_files=args.eval_file)["train"]
        if args.max_samples:
            eval_dataset = eval_dataset.select(range(min(args.max_samples // 5, len(eval_dataset))))
        eval_dataset = eval_dataset.map(tokenize_fn, remove_columns=eval_dataset.column_names)
        print(f"  평가 샘플: {len(eval_dataset)}")

    data_collator = CausalLMDataCollator(tokenizer=tokenizer)

    # TrainingArguments
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
        fp16=True,  # ROCm에서 FP16 사용
        seed=args.seed,
        report_to=[],
        optim="adamw_torch",  # 기본 optimizer
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        gradient_checkpointing=args.gradient_checkpointing,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    print("\n" + "=" * 60)
    print("학습 시작!")
    print("=" * 60)

    trainer.train()

    print("\n모델 저장 중...")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print("\n" + "=" * 60)
    print("학습 완료!")
    print(f"모델 저장 위치: {args.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
