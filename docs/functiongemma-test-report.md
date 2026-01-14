# FunctionGemma Test Report (Home IoT Demo)

Korean: [functiongemma-test-report.ko.md](functiongemma-test-report.ko.md)

This document captures LoRA fine-tuning results and evaluation notes for this
project. It also serves as a reproducibility checklist for similar tests.

## Model / Adapter
- Base model: `google/functiongemma-270m-it`
- LoRA adapter (in repo):
  - `training/output_lora/adapter_model.safetensors`
  - `training/output_lora/adapter_config.json`
- External backups are optional and not stored in this repo.

## Training Data Summary
- Full JSONL: `training/data/train_home_ko.jsonl` (3167 lines)
- Train: `training/data/train_home_ko.train.jsonl` (2841 lines)
- Validation: `training/data/train_home_ko.val.jsonl` (326 lines)

## Training Run Summary
- Start time: 2026-01-13T17:11:41+09:00
- Epochs: 3
- max_seq_length: 512
- per_device_train_batch_size: 1
- gradient_accumulation_steps: 16
- learning_rate: 1e-4
- attn_implementation: eager
- train_loss: 0.0772939051
- eval_loss: 0.0261247084 (epoch 2.25)
- train_runtime: 6274.1s (~1h44m)
- Logs:
  - `training/logs/finetune_20260113_171141.log`

## Raspberry Pi Test (CPU-only)
- Full report: `docs/functiongemma-test-report-raspberrypi.md`

## How to Test
1) Load adapter and run prompts
```bash
training/venv/bin/python training/quick_infer.py \
  --adapter_dir training/output_lora \
  --prompt_file docs/functiongemma-test-prompts.txt
```

2) Demo commands
- docs/demo-commands.md

## Result Summary (2026-01-13)
Summary based on 28 evaluation prompts.

Working well
- Zone cleaning (kitchen/bedroom), app launch (YouTube/Netflix), relative
  volume/temperature adjustments, curtain percent, fan speed, audio play/pause.

Remaining issues (minor for demo)
1) "거실 청소 시작해줘" -> extra calls before `vacuum_clean_zone(living_room)`
2) "조명 색온도 3000으로" -> mapped to `light_set_brightness(3000)`
3) "TV 켜고 에어컨 26도, 조명 50%, 커튼 닫아줘" -> extra `light_adjust_brightness`
4) "청소기 멈춰" -> interpreted as pause (stop vs pause)
5) "영화 볼 준비해줘" -> no scenario function; falls back to TV on + channel 1

## Related
- demo-commands.md
- functiongemma-test-report-raspberrypi.md
- functiongemma-test-prompts.txt
- fine-tuning.md
