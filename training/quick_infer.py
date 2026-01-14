#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoProcessor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.append(str(BACKEND_DIR))

from home_controller import HOME_FUNCTION_SCHEMAS  # noqa: E402
from function_gemma import BASE_SYSTEM_PROMPT_LINES  # noqa: E402

DEFAULT_PROMPTS = [
    "로봇 청소기 끄고 환풍기 켜",
    "주방 청소해줘",
    "TV 켜고 유튜브 실행해줘",
    "에어컨 24도로 맞추고 팬은 강으로",
    "조명 밝기 40%로 하고 색온도 3000으로",
    "TV 켜고 에어컨 26도, 조명 50%, 커튼 닫아줘",
]

CALL_BLOCK_RE = re.compile(
    r"<start_(?:of_)?function_call>(.*?)<end_(?:of_)?function_call>",
    re.DOTALL,
)


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick LoRA inference check")
    parser.add_argument("--model_id", default="google/functiongemma-270m-it")
    parser.add_argument("--adapter_dir", default="training/output_lora")
    parser.add_argument(
        "--no_adapter",
        action="store_true",
        help="Disable loading LoRA adapter and run base model only",
    )
    parser.add_argument("--prompt", action="append", default=[])
    parser.add_argument("--prompt_file", default=None)
    parser.add_argument("--max_new_tokens", type=int, default=256)
    parser.add_argument(
        "--attn_implementation",
        default="eager",
        choices=["eager", "sdpa", "flash_attention_2"],
    )
    parser.add_argument(
        "--dtype",
        default="fp32",
        choices=["fp32", "fp16", "bf16"],
    )
    parser.add_argument("--device", default=None)
    parser.add_argument(
        "--output_json",
        default=None,
        help="Write JSONL results to the given path",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout output (useful with --output_json)",
    )
    return parser.parse_args()


def select_device(device_arg: str | None) -> torch.device:
    if device_arg:
        return torch.device(device_arg)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def select_dtype(dtype_arg: str, device: torch.device) -> torch.dtype:
    if dtype_arg == "bf16":
        return torch.bfloat16
    if dtype_arg == "fp16":
        return torch.float16
    return torch.float32


def read_prompts(args: argparse.Namespace) -> List[str]:
    prompts: List[str] = []
    if args.prompt:
        prompts.extend([p.strip() for p in args.prompt if p.strip()])
    if args.prompt_file:
        for line in Path(args.prompt_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                prompts.append(line)
    return prompts or DEFAULT_PROMPTS


def coerce_value(value: str) -> object:
    value = value.strip()
    if value.lstrip("-").isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def parse_parameters(params_str: str) -> dict:
    params: dict = {}
    if not params_str.strip():
        return params
    for key, value in re.findall(r"(\w+):<escape>([^<]*)<escape>", params_str):
        params[key] = coerce_value(value)
    return params


def parse_function_calls(output: str) -> List[dict]:
    segments = CALL_BLOCK_RE.findall(output)
    if not segments and "call:" in output:
        segments = [output]

    calls: List[dict] = []
    for segment in segments:
        text = segment.strip()
        if text.startswith("call:"):
            text = text[5:]
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start == -1 or brace_end == -1 or brace_end < brace_start:
            continue
        function_name = text[:brace_start].strip()
        params_str = text[brace_start + 1 : brace_end]
        calls.append(
            {
                "function_name": function_name,
                "parameters": parse_parameters(params_str),
            }
        )
    return calls


def main() -> None:
    args = parse_args()
    load_env(PROJECT_ROOT / ".env")

    device = select_device(args.device)
    dtype = select_dtype(args.dtype, device)

    processor = AutoProcessor.from_pretrained(args.model_id, trust_remote_code=True)
    tokenizer = getattr(processor, "tokenizer", processor)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=dtype,
        attn_implementation=args.attn_implementation,
        trust_remote_code=True,
    )
    if not args.no_adapter:
        model = PeftModel.from_pretrained(model, args.adapter_dir)
    model.to(device)
    model.eval()

    system_prompt = "\n".join(BASE_SYSTEM_PROMPT_LINES)
    prompts = read_prompts(args)

    output_path = Path(args.output_json) if args.output_json else None
    output_handle = None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_handle = output_path.open("w", encoding="utf-8")

    for idx, prompt in enumerate(prompts, start=1):
        messages = [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        inputs = processor.apply_chat_template(
            messages,
            tools=HOME_FUNCTION_SCHEMAS,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=False,
            )

        generated_ids = output_ids[0][inputs["input_ids"].shape[1] :]
        output_text = tokenizer.decode(generated_ids, skip_special_tokens=False).strip()
        calls = parse_function_calls(output_text)

        result = {
            "index": idx,
            "prompt": prompt,
            "raw_output": output_text,
            "parsed_calls": calls,
            "model_id": args.model_id,
            "adapter_dir": None if args.no_adapter else args.adapter_dir,
        }

        if output_handle:
            output_handle.write(json.dumps(result, ensure_ascii=False) + "\n")

        if not args.quiet:
            print("=" * 80)
            print(f"[{idx}] USER: {prompt}")
            print("RAW OUTPUT:")
            print(output_text)
            print("PARSED CALLS:")
            print(json.dumps(calls, ensure_ascii=False, indent=2))

    if output_handle:
        output_handle.close()


if __name__ == "__main__":
    main()
