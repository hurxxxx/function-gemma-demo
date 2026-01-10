# LoRA 파인튜닝 (FunctionGemma)

## 설치
1) GPU에 맞는 PyTorch 설치 (CUDA 또는 ROCm)
2) 나머지 패키지 설치
```bash
pip install -r training/requirements-train.txt
```

## 데이터
- JSONL 파일
- 필드: `messages` (developer/user/assistant)
- 예시: `training/data/train_ko_sample.jsonl`

## 학습
```bash
python training/finetune_lora.py \
  --train_file training/data/train_ko_sample.jsonl \
  --output_dir training/output_lora \
  --num_train_epochs 3 \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 8 \
  --learning_rate 1e-4
```

## 결과
- `training/output_lora`에 LoRA 어댑터 저장
- 추론 시 베이스 모델 + 어댑터 로드
