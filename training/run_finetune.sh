#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/training/logs"
OUT_DIR="$ROOT/training/output_lora"
TS="$(date +%Y%m%d_%H%M%S)"
RUN_LOG="$LOG_DIR/finetune_${TS}.log"
TAIL_LOG="$OUT_DIR/train.log"
USE_FP16="${FG_USE_FP16:-0}"
FP16_FLAG=""
if [ "$USE_FP16" = "1" ]; then
  FP16_FLAG="--fp16"
fi

mkdir -p "$LOG_DIR" "$OUT_DIR"

if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ROOT/.env"
  set +a
fi

{
  echo "=== start $(date -Is) ==="
  echo "log_file=${RUN_LOG}"
  echo "tail_log=${TAIL_LOG}"
  echo "HSA_ENABLE_SDMA=0"
  echo "TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1"
  echo "PYTHONUNBUFFERED=1"
  echo "PYTHONFAULTHANDLER=1"
  echo "command=finetune_lora.py (see below)"
} | tee -a "$RUN_LOG" "$TAIL_LOG"

RUN_CMD=$(cat <<EOF
export HSA_ENABLE_SDMA=0
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
export PYTHONUNBUFFERED=1
export PYTHONFAULTHANDLER=1
stdbuf -oL -eL "$ROOT/training/venv/bin/python" -u "$ROOT/training/finetune_lora.py" \
  --train_file "$ROOT/training/data/train_home_ko.train.jsonl" \
  --eval_file "$ROOT/training/data/train_home_ko.val.jsonl" \
  --output_dir "$ROOT/training/output_lora" \
  --num_train_epochs 3 \
  --max_seq_length 512 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --learning_rate 1e-4 \
  --logging_steps 20 \
  --save_steps 200 \
  $FP16_FLAG \
  --attn_implementation eager \
  2>&1 | tee -a "$RUN_LOG" "$TAIL_LOG"
EOF
)

nohup bash -lc "$RUN_CMD" >/dev/null 2>&1 &
PID=$!
echo "$PID" > "$OUT_DIR/finetune.pid"
echo "PID=$PID"
echo "LOG_FILE=$RUN_LOG"
