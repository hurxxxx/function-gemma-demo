# FunctionGemma Home IoT LoRA Output

Base model: google/functiongemma-270m-it

Artifacts moved out of the repo:
- /projects/function-gemma-demo-artifacts/finetune_20260113_140359
  - adapter_model.safetensors
  - adapter_config.json
  - checkpoint-400, checkpoint-516
  - train.log
  - finetune_20260113_140359.log

Run summary (2026-01-13)
- train file: training/data/train_home_ko.train.jsonl
- eval file: training/data/train_home_ko.val.jsonl
- epochs: 3
- max_seq_length: 512
- per_device_train_batch_size: 1
- gradient_accumulation_steps: 16
- learning_rate: 1e-4
- attn_implementation: eager
- final train_loss: 0.0743384244
- last eval_loss: 0.0255804248 (epoch 2.33)
- train_runtime: 8453.7s (~2h20m)

Quick inference
```bash
training/venv/bin/python training/quick_infer.py \
  --adapter_dir /projects/function-gemma-demo-artifacts/finetune_20260113_140359
```
