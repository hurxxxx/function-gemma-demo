# LoRA 파인튜닝 (FunctionGemma)

## 설치
1) GPU에 맞는 PyTorch 설치 (CUDA 또는 ROCm)
2) 나머지 패키지 설치
```bash
pip install -r training/requirements-train.txt
```

## 인증 (Gated 모델)
`.env`에 HF 토큰을 설정하면 학습/추론에서 자동으로 참조합니다.
```
HUGGINGFACE_HUB_TOKEN=...
HF_TOKEN=...
```

## 데이터
- JSONL 파일
- 필드: `messages` (developer/user/assistant)
- 예시: `training/data/train_home_ko.train.jsonl` / `training/data/train_home_ko.val.jsonl`

## 학습
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

로그 보존용 스크립트:
```bash
training/run_finetune.sh
```
FP16을 켜려면:
```bash
FG_USE_FP16=1 training/run_finetune.sh
```

## 결과
- `training/output_lora`에 LoRA 어댑터 저장
- 추론 시 베이스 모델 + 어댑터 로드

## 간단 추론 테스트
```bash
training/venv/bin/python training/quick_infer.py --adapter_dir training/output_lora
```
