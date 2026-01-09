# FunctionGemma 사용 핵심 정리 (HF 모델 카드 기반)

출처: https://huggingface.co/google/functiongemma-270m-it

## 핵심 요약
- FunctionGemma는 **함수 호출 전용 기반 모델**이며, 일반 대화형 모델로 쓰는 것을 의도하지 않음.
- **도메인/태스크에 맞춘 파인튜닝이 권장**됨(특히 멀티턴 시나리오).
- Gemma 3 기반 아키텍처이며 **FunctionGemma 전용 채팅 포맷**을 사용.
- **Developer 역할 메시지가 필수**로 언급됨(함수 호출 모드 활성화 목적).
- 출력은 **함수 호출 토큰 형식**으로 반환됨:
  - `<start_function_call>call:함수명{param:<escape>값<escape>}<end_function_call>`
- 입력 컨텍스트 최대 32K 토큰.
- **Gated 모델**이므로 HF 로그인/라이선스 승인 필요.

## 다국어 입력 처리 (현재 프로젝트 설정)
- 사용자 입력을 **로컬 번역 모델로 영어로 변환**한 뒤 FunctionGemma에 전달함.
- **규칙 기반/키워드 기반 후처리는 사용하지 않음**(모델 출력만 사용).
- 번역 사용 여부:
  - `FG_TRANSLATION_ENABLED=1` (기본값: 1)
  - `FG_TRANSLATION_ENABLED=0` 으로 번역 비활성화 가능
- 기본 번역 모델: `Helsinki-NLP/opus-mt-mul-en` (언어별 전용 모델 우선 사용)
- 번역 관련 환경 변수:
  - `FG_TRANSLATION_MODEL` (기본값: `Helsinki-NLP/opus-mt-mul-en`)
  - `FG_TRANSLATION_MODEL_MAP` (JSON, 언어 코드별 모델 지정)
  - `FG_TRANSLATION_MAX_TOKENS` (기본값: 128)
- 270m-it 모델은 일부 문맥에서 오동작 가능성이 있어, **정확도를 더 올리려면 파인튜닝 또는 더 큰 모델**을 고려해야 함.

## 필수 사용 패턴
### 1) tools(JSON schema) 정의
```python
weather_function_schema = {
    "type": "function",
    "function": {
        "name": "get_current_temperature",
        "description": "Gets the current temperature for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    }
}
```

### 2) developer 역할 메시지로 시스템 지시
```python
messages = [
    {
        "role": "developer",
        "content": "You are a model that can do function calling with the following functions"
    },
    {"role": "user", "content": "What's the temperature in London?"}
]

inputs = processor.apply_chat_template(
    messages,
    tools=[weather_function_schema],
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt"
)
```

### 3) 생성 및 디코딩
```python
out = model.generate(
    **inputs.to(model.device),
    pad_token_id=processor.eos_token_id,
    max_new_tokens=128
)
output = processor.decode(out[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
print(output)
# <start_function_call>call:get_current_temperature{location:<escape>London<escape>}<end_function_call>
```

## 설치/버전 유의사항
- Gemma 3(`gemma3_text`) 아키텍처를 인식하려면 **Transformers 최신 버전**이 필요함.
  - 이 프로젝트에서는 `transformers==4.57.3`로 통일.
- CPU 전용 실행 시 예시:
```python
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

processor = AutoProcessor.from_pretrained(
    "google/functiongemma-270m-it",
    device_map="cpu",
    trust_remote_code=True
)
model = AutoModelForCausalLM.from_pretrained(
    "google/functiongemma-270m-it",
    torch_dtype=torch.float32,
    device_map="cpu",
    trust_remote_code=True
)
```

## 구현 체크리스트
- [ ] developer 역할 메시지를 사용했는가
- [ ] tools(JSON schema)를 `apply_chat_template`에 전달했는가
- [ ] 출력 포맷(`<start_function_call>...`) 파싱 로직이 있는가
- [ ] `transformers>=4.57` 사용 중인가
- [ ] HF 로그인/라이선스 승인이 완료되었는가

## 참고 문서
- FunctionGemma 모델 카드 (HF): https://huggingface.co/google/functiongemma-270m-it
- FunctionGemma 개요 (Google AI): https://ai.google.dev/gemma/docs/functiongemma
- Gemma Cookbook (FunctionGemma 파인튜닝 예제): https://github.com/google-gemini/gemma-cookbook/blob/main/FunctionGemma/%5BFunctionGemma%5DFinetune_FunctionGemma_270M_for_Mobile_Actions_with_Hugging_Face.ipynb
- Mobile Actions 데이터셋: https://huggingface.co/datasets/google/mobile-actions
- Kaggle 모델 페이지: https://www.kaggle.com/models/google/functiongemma/
