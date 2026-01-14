# FunctionGemma LoRA Fine-tuning Guide (Korean Input)

Korean: [functiongemma-finetune.ko.md](functiongemma-finetune.ko.md)

## Goal
- Keep Korean input as-is while improving function-calling accuracy.
- Train on GPU machines, run **CPU inference** on low-power devices if needed.

## Prerequisites
- Hugging Face token (gated model access)
- `.env` token (`HUGGINGFACE_HUB_TOKEN` or `HF_TOKEN`)
- GPU machine (CUDA or ROCm)
- Install `training/requirements-train.txt`

## HF Token
Example `.env`:
```
HUGGINGFACE_HUB_TOKEN=...
HF_TOKEN=...
```

Session notes and failures are tracked in `docs/fine-tuning.md`.

## Data Format (JSONL)
One sample per line:
```jsonl
{"messages":[
  {"role":"developer","content":"You are a model that can do function calling with the following functions"},
  {"role":"user","content":"온도 2도 올려줘"},
  {"role":"assistant","content":"<start_function_call>call:adjust_temperature{delta:<escape>2<escape>}<end_function_call>"}
]}
```

Notes:
- `developer` message is required.
- Use the **same developer message** as inference for stability.
- Samples can use a short developer message for simplicity.
- Use `<start_function_call>...<end_function_call>` format.
- Wrap string parameters with `<escape>`.

## Training Example
```bash
python training/finetune_lora.py \
  --train_file training/data/train_home_ko.train.jsonl \
  --eval_file training/data/train_home_ko.val.jsonl \
  --output_dir training/output_lora \
  --num_train_epochs 3 \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 8 \
  --learning_rate 1e-4
```

Use `training/run_finetune.sh` for logging and env setup.
Enable FP16 with `FG_USE_FP16=1` if needed.

## Post-training Inference (CPU)
```python
from transformers import AutoProcessor, AutoModelForCausalLM
from peft import PeftModel
import torch

model_id = "google/functiongemma-270m-it"
adapter_path = "training/output_lora"

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
base = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="cpu",
    torch_dtype=torch.float32,
    trust_remote_code=True
)
model = PeftModel.from_pretrained(base, adapter_path)
model.eval()
```

## Recommended Data Coverage
- +/- 1~2 degrees, absolute temperature, mode, fan speed, power on/off
- Phrase variations (e.g., "덥다", "춥다", "아이들이 땀 난다")
- Prefer single-turn samples for stability

## References
- FunctionGemma official docs: https://ai.google.dev/gemma/docs/functiongemma

## Related
- functiongemma-usage.md
- fine-tuning.md
- functiongemma-test-report.md
