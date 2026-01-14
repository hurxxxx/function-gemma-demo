---
base_model: google/functiongemma-270m-it
library_name: peft
---
# FunctionGemma Home IoT LoRA 결과물

English: [README.md](README.md)

Base model: google/functiongemma-270m-it

리포지토리에 포함된 파일:
- adapter_model.safetensors
- adapter_config.json

외부 백업(선택):
- `FG_OUTPUT_DIR`로 리포지토리 밖에 로그/체크포인트 저장

새 실행을 외부 경로로 저장하려면:
```
FG_OUTPUT_DIR=/projects/function-gemma-demo-artifacts/finetune_YYYYMMDD_HHMMSS \
  training/run_finetune.sh
```

실행 요약 (2026-01-13 17:11)
- train file: training/data/train_home_ko.train.jsonl
- eval file: training/data/train_home_ko.val.jsonl
- epochs: 3
- max_seq_length: 512
- per_device_train_batch_size: 1
- gradient_accumulation_steps: 16
- learning_rate: 1e-4
- attn_implementation: eager
- final train_loss: 0.0772939051
- last eval_loss: 0.0261247084 (epoch 2.25)
- train_runtime: 6274.1s (~1h44m)

빠른 추론
```bash
training/venv/bin/python training/quick_infer.py \
  --adapter_dir training/output_lora
```

### Framework versions
- PEFT 0.14.0
