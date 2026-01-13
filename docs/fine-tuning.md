# Fine-tuning Notes (Strix Halo 395 / gfx1151)

## Official references (ROCm Ryzen)
- Compatibility matrix (Linux): https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityryz/native_linux/native_linux_compatibility.html
  - ROCm 7.1.1 supports gfx1150/gfx1151 (Ryzen AI Max+ 395 series)
  - PyTorch 2.9 / Python 3.12 / FP16 listed in the ROCm 7.1.1 matrix
- Install PyTorch for Ryzen APUs: https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installryz/native_linux/install-pytorch.html
  - AMD wheel URLs are hosted at repo.radeon.com
  - AOTriton opt-in: TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
- Ryzen limitations (ROCm 7.1.1): https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/limitations/limitationsryz.html

## System snapshot (2026-01-13, this machine)
- OS: Ubuntu 24.04.3 LTS (noble)
- Kernel: 6.14.0-1017-oem
- GPU: AMD Radeon Graphics (STRXLGEN), GFX version gfx1151
- CPU (rocminfo): AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
- ROCm: 7.1.1.70101-38~24.04 (rocm meta package)
- Driver version (rocm-smi): 6.14.0-1017-oem
- Python (venv): 3.12.3
- torch: 2.9.1+rocm7.1.1.git351ff442
- transformers: 4.57.3
- peft: 0.14.0
- datasets: 3.2.0

Validation commands:
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

## Installed ROCm/AMDGPU packages (key ones)
The system has the AMD repo and ROCm 7.1.1 stack installed. Key packages
observed via `dpkg -l`:
- amdgpu-core 1:7.1.70101-2255337.24.04
- amdgpu-install 30.20.1.0.30200100-2255209.24.04
- rocm 7.1.1.70101-38~24.04
- rocm-core 7.1.1.70101-38~24.04
- rocm-hip 7.1.1.70101-38~24.04
- rocm-smi-lib 7.8.0.70101-38~24.04
- rocminfo 1.0.0.70101-38~24.04
- hip-runtime-amd 7.1.52802.70101-38~24.04
- miopen-hip 3.5.1.70101-38~24.04

Full check:
```bash
dpkg -l | rg -n "rocm|hip|hsa|amdgpu"
```

## Project runtime settings (applied)
Environment variables used for stability in this project:
```
HSA_ENABLE_SDMA=0
TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
PYTHONUNBUFFERED=1
PYTHONFAULTHANDLER=1
```

Optional:
- `FG_USE_FP16=1` to enable fp16 in `training/run_finetune.sh` (default is FP32).

## Auth / gated model setup
Create `.env` at the repo root:
```
HUGGINGFACE_HUB_TOKEN=YOUR_TOKEN
HF_TOKEN=YOUR_TOKEN
```
`training/run_finetune.sh` auto-sources `.env` before running.

## Training command (applied)
`training/run_finetune.sh` launches:
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

Notable code-path settings:
- `attn_implementation=eager`
- `device_map` removed (single-device load)
- FP32 default (FP16 can produce NaNs)

## Logging and outputs
- Per-run logs: `training/logs/finetune_YYYYMMDD_HHMMSS.log`
- Append-only log: `training/output_lora/train.log`
- PID file: `training/output_lora/finetune.pid`
- Adapter output: `training/output_lora/adapter_model.safetensors`,
  `training/output_lora/adapter_config.json`
- Stored artifacts (outside repo): `/projects/function-gemma-demo-artifacts/finetune_20260113_140359`

## Service tweaks
To reduce GPU faults, `smbgate-backend.service` was disabled:
```bash
systemctl is-enabled smbgate-backend.service
systemctl is-active smbgate-backend.service
```

If needed:
```bash
sudo systemctl disable --now smbgate-backend.service
```

## Known failures / mitigations
- 2026-01-13: HIP illegal memory access during training (step 1/516); process stuck in D state; required reboot.
- Mitigations applied:
  - Use attn_implementation=eager and single-device load (device_map removed).
  - Reduce max_seq_length to 512, batch size 1, grad accumulation 16.
  - Disable smbgate-backend service to avoid GPU page faults.
  - Use HSA_ENABLE_SDMA=0 and AOTriton experimental flag.
  - FP16로 loss/grad NaN 발생 → 기본 실행은 FP32 (필요 시 `FG_USE_FP16=1`로 FP16 활성화).

## Latest run (completed)
- Start time: 2026-01-13T14:03:59+09:00
- Status: completed (FP32)
- PID: 59783 (exited)
- Log files: training/logs/finetune_20260113_140359.log, training/output_lora/train.log
- Output: training/output_lora/adapter_model.safetensors, training/output_lora/adapter_config.json
- Final metrics: train_loss 0.0743384244, eval_loss 0.0255804248 (epoch 2.33), train_runtime 8453.7s
- Notes: HF token sourced from `.env` via `training/run_finetune.sh`.

## Quick inference check
```bash
training/venv/bin/python training/quick_infer.py --adapter_dir training/output_lora
```
