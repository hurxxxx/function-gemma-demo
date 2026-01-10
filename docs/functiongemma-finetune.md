# FunctionGemma LoRA 파인튜닝 가이드 (한국어 입력)

## 목표
- 한국어 입력을 그대로 사용하면서 함수 호출 정확도를 높입니다.
- 파인튜닝은 GPU 머신에서 진행하고, 라즈베리파이4에서는 **CPU 추론**만 수행합니다.

## 준비물
- Hugging Face 토큰 (gated 모델 접근 필요)
- GPU 머신 (CUDA 또는 ROCm)
- `training/requirements-train.txt` 설치

## 데이터 포맷 (JSONL)
한 줄에 하나의 샘플을 넣습니다.
```jsonl
{"messages":[
  {"role":"developer","content":"You are a model that can do function calling with the following functions"},
  {"role":"user","content":"온도 2도 올려줘"},
  {"role":"assistant","content":"<start_function_call>call:adjust_temperature{delta:<escape>2<escape>}<end_function_call>"}
]}
```

주의사항:
- `developer` 메시지는 필수입니다.
- 실제 추론에 사용하는 개발자 메시지와 **동일한 문구**를 쓰는 것이 안정적입니다.
- 샘플 데이터는 간단화를 위해 짧은 developer 문구만 사용합니다.
- 함수 호출 형식은 `<start_function_call>...<end_function_call>`을 사용합니다.
- 문자열 파라미터는 `<escape>`로 감싸야 합니다.

## 학습 실행 예시
```bash
python training/finetune_lora.py \
  --train_file training/data/train_ko_sample.jsonl \
  --output_dir training/output_lora \
  --num_train_epochs 3 \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 8 \
  --learning_rate 1e-4
```

## 파인튜닝 후 추론 (CPU)
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

## 권장 데이터 구성
- 1~2도 올려/내려, 온도 설정, 현재 온도 질문, 모드 변경, 팬 속도 변경, 전원 on/off
- 문장 다양화 (예: “덥다”, “춥다”, “아이들이 땀 난다” 등)
- 단일턴 위주 (FunctionGemma는 멀티턴에 약함)

## 참고
- FunctionGemma 공식 문서: https://ai.google.dev/gemma/docs/functiongemma
