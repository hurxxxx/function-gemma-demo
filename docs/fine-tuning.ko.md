# 파인튜닝 노트 (Strix Halo 395 / gfx1151)

English: [fine-tuning.md](fine-tuning.md)

## 공식 참고 링크 (ROCm Ryzen)
- 호환성 매트릭스 (Linux): https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityryz/native_linux/native_linux_compatibility.html
  - ROCm 7.1.1에서 gfx1150/gfx1151 지원 (Ryzen AI Max+ 395 계열)
  - ROCm 7.1.1 매트릭스에 PyTorch 2.9 / Python 3.12 / FP16 표기
- Ryzen APU용 PyTorch 설치: https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installryz/native_linux/install-pytorch.html
  - AMD wheel URL은 repo.radeon.com 제공
  - AOTriton opt-in: TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
- Ryzen 제한사항 (ROCm 7.1.1): https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/limitations/limitationsryz.html

## 시스템 스냅샷 (2026-01-13, 이 머신)
- OS: Ubuntu 24.04.3 LTS (noble)
- Kernel: 6.14.0-1017-oem
- GPU: AMD Radeon Graphics (STRXLGEN), GFX 버전 gfx1151
- CPU (rocminfo): AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
- ROCm: 7.1.1.70101-38~24.04 (rocm 메타 패키지)
- Driver 버전 (rocm-smi): 6.14.0-1017-oem
- Python (venv): 3.12.3
- torch: 2.9.1+rocm7.1.1.git351ff442
- transformers: 4.57.3
- peft: 0.14.0
- datasets: 3.2.0

검증 명령:
```bash
uname -r
lsb_release -a
rocm-smi --showproductname --showdriverversion --showuse
rocminfo | rg -n "gfx|Name:" | head -n 20
training/venv/bin/python - <<'PY'
import json, platform, sys
import torch, transformers, peft, datasets
print(json.dumps({
  "python": sys.version.split()[0],
  "platform": platform.platform(),
  "torch": torch.__version__,
  "transformers": transformers.__version__,
  "peft": peft.__version__,
  "datasets": datasets.__version__,
  "cuda_available": torch.cuda.is_available(),
}, indent=2))
PY
```

## 설치된 ROCm/AMDGPU 패키지 (주요 항목)
AMD repo 및 ROCm 7.1.1 스택 설치 확인. `dpkg -l` 기준:
- amdgpu-core 1:7.1.70101-2255337.24.04
- amdgpu-install 30.20.1.0.30200100-2255209.24.04
- rocm 7.1.1.70101-38~24.04
- rocm-core 7.1.1.70101-38~24.04
- rocm-hip 7.1.1.70101-38~24.04
- rocm-smi-lib 7.8.0.70101-38~24.04
- rocminfo 1.0.0.70101-38~24.04
- hip-runtime-amd 7.1.52802.70101-38~24.04
- miopen-hip 3.5.1.70101-38~24.04

전체 확인:
```bash
dpkg -l | rg -n "rocm|hip|hsa|amdgpu"
```

## 프로젝트 런타임 설정 (적용됨)
안정화를 위해 사용한 환경 변수:
```
HSA_ENABLE_SDMA=0
TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
PYTHONUNBUFFERED=1
PYTHONFAULTHANDLER=1
```

옵션:
- `FG_USE_FP16=1`로 FP16 활성화 (`training/run_finetune.sh` 기본은 FP32)

## 인증 / Gated 모델 설정
프로젝트 루트에 `.env` 생성:
```
HUGGINGFACE_HUB_TOKEN=YOUR_TOKEN
HF_TOKEN=YOUR_TOKEN
```
`training/run_finetune.sh` 실행 시 `.env`를 자동 로드합니다.

## 학습 실행 커맨드 (적용됨)
`training/run_finetune.sh`에서 실행되는 명령:
```bash
python -u training/finetune_lora.py \
  --train_file training/data/train_home_ko.train.jsonl \
  --eval_file training/data/train_home_ko.val.jsonl \
  --output_dir training/output_lora \
  --num_train_epochs 3 \
  --max_seq_length 512 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --learning_rate 1e-4 \
  --logging_steps 20 \
  --save_steps 200 \
  --attn_implementation eager
```

코드 경로 설정 요약:
- `attn_implementation=eager`
- `device_map` 제거 (단일 디바이스 로드)
- 기본 FP32 (FP16은 NaN 가능)

## 로그/결과
- 실행 로그: `training/logs/finetune_YYYYMMDD_HHMMSS.log`
- 누적 로그: `training/output_lora/train.log` (기본)
- PID 파일: `training/output_lora/finetune.pid`
- 어댑터 출력: `training/output_lora/adapter_model.safetensors`,
  `training/output_lora/adapter_config.json`
- 외부 백업(선택): `FG_OUTPUT_DIR`로 리포지토리 밖에 저장 가능

## 서비스 설정
GPU fault 감소를 위해 `smbgate-backend.service` 비활성화:
```bash
systemctl is-enabled smbgate-backend.service
systemctl is-active smbgate-backend.service
```

필요 시:
```bash
sudo systemctl disable --now smbgate-backend.service
```

## 알려진 실패 / 대응
- 2026-01-13: HIP illegal memory access, D 상태로 고정되어 재부팅 필요
- 대응:
  - `attn_implementation=eager` 사용
  - `max_seq_length=512`, `per_device_train_batch_size=1`, `gradient_accumulation_steps=16`
  - `smbgate-backend.service` 비활성화
  - `HSA_ENABLE_SDMA=0`, AOTriton experimental flag
  - 기본 FP32 (FP16은 NaN 가능)

## 최신 학습 (완료)
- 시작 시각: 2026-01-13T17:11:41+09:00
- 상태: 완료 (FP32)
- PID: 225424 (종료됨)
- 로그: training/logs/finetune_20260113_171141.log
- 출력: training/output_lora/adapter_model.safetensors, training/output_lora/adapter_config.json
- 최종 지표: train_loss 0.0772939051, eval_loss 0.0261247084 (epoch 2.25), train_runtime 6274.1s
- 비고: `.env`의 HF 토큰을 `training/run_finetune.sh`가 자동 로드

## 빠른 추론 테스트
```bash
training/venv/bin/python training/quick_infer.py --adapter_dir training/output_lora
```

## 관련 문서
- functiongemma-finetune.ko.md
- functiongemma-test-report.ko.md
- demo-commands.ko.md
