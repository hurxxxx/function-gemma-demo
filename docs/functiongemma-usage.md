# FunctionGemma 사용 핵심 정리

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
  - `.env`에 `HUGGINGFACE_HUB_TOKEN`(또는 `HF_TOKEN`)을 설정해 학습/추론에서 자동 참조.

---

## 멀티턴 함수 호출 (Multi-Turn Function Calling)

### 공식 멀티턴 플로우
FunctionGemma는 복합 명령을 처리하기 위한 멀티턴 함수 호출을 지원합니다.

```
[Turn 1] developer: 시스템 프롬프트 + 함수 스키마
[Turn 2] user: "TV 켜고 조명 꺼줘"
[Turn 3] assistant: <start_function_call>call:tv_power_on{}<end_function_call>
                    <start_function_call>call:light_power_off{}<end_function_call>
[Turn 4] tool: [
    {"name": "tv_power_on", "response": {"success": true}},
    {"name": "light_power_off", "response": {"success": true}}
]
[Turn 5] assistant: "TV를 켜고 조명을 껐습니다."
```

### 메시지 역할 정의
| Role | 설명 |
|------|------|
| `developer` | 시스템 프롬프트, 함수 호출 모드 활성화 (필수) |
| `user` | 사용자 음성/텍스트 명령 |
| `assistant` | 모델의 함수 호출 출력 |
| `tool` | 함수 실행 결과 (복수 결과 가능) |

### 복수 함수 호출 출력 형식
단일 응답에서 여러 함수를 연속으로 호출:
```
<start_function_call>call:function1{}<end_function_call>
<start_function_call>call:function2{param:<escape>value<escape>}<end_function_call>
```

### tool role로 결과 피드백
```python
messages.append({
    "role": "tool",
    "content": [
        {"name": "tv_power_on", "response": {"success": True}},
        {"name": "light_power_off", "response": {"success": True}}
    ]
})
```

---

## 다국어 입력 처리 (현재 프로젝트 설정)
- 사용자 입력을 **한국어 그대로 FunctionGemma에 전달**함.
- **규칙 기반/키워드 기반 후처리는 사용하지 않음**(모델 출력만 사용).
- 270m-it 모델은 한국어에서 일부 문맥 오동작이 있어, **정확도를 더 올리려면 파인튜닝(LoRA) 권장**.
- 파인튜닝 가이드: `docs/functiongemma-finetune.md`

---

## 필수 사용 패턴

### 1) tools(JSON schema) 정의
```python
function_schema = {
    "type": "function",
    "function": {
        "name": "tv_power_on",
        "description": "TV 전원을 켭니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
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
    {"role": "user", "content": "TV 켜줘"}
]

inputs = processor.apply_chat_template(
    messages,
    tools=[function_schema],
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
    max_new_tokens=256  # 복합 명령을 위해 증가
)
output = processor.decode(out[0][len(inputs["input_ids"][0]):], skip_special_tokens=False)
# <start_function_call>call:tv_power_on{}<end_function_call>
```

### 4) 함수 호출 파싱
```python
import re

def parse_function_calls(output: str) -> list[dict]:
    calls = []
    segments = re.findall(
        r"<start_(?:of_)?function_call>(.*?)<end_(?:of_)?function_call>",
        output,
        flags=re.DOTALL,
    )
    for segment in segments:
        # call:function_name{params} 형식 파싱
        text = segment.strip()
        if text.startswith("call:"):
            text = text[5:]
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1:
            function_name = text[:brace_start].strip()
            params_str = text[brace_start+1:brace_end]
            params = parse_parameters(params_str)
            calls.append({"function_name": function_name, "parameters": params})
    return calls

def parse_parameters(params_str: str) -> dict:
    if not params_str:
        return {}
    # <escape>value<escape> 형식 파싱
    params = {}
    for key, value in re.findall(r"(\w+):<escape>([^<]*)<escape>", params_str):
        params[key] = coerce_value(value)
    return params
```

---

## Few-Shot 예시 구성 (선택)

이 프로젝트에서는 **런타임 few-shot을 사용하지 않고** 파인튜닝으로 정확도를 맞춥니다.
few-shot은 포맷 검증이나 빠른 프로토타입에만 제한적으로 사용하세요.

```python
few_shot_messages = [
    {"role": "user", "content": "에어컨 켜줘"},
    {"role": "assistant", "content": "<start_function_call>call:ac_power_on{}<end_function_call>"},
    {"role": "user", "content": "TV 9번 채널로"},
    {"role": "assistant", "content": "<start_function_call>call:tv_set_channel{channel:<escape>9<escape>}<end_function_call>"},
    # 복합 명령 예시
    {"role": "user", "content": "TV 켜고 조명 꺼줘"},
    {"role": "assistant", "content": "<start_function_call>call:tv_power_on{}<end_function_call>\n<start_function_call>call:light_power_off{}<end_function_call>"},
]

messages = [
    {"role": "developer", "content": system_prompt},
    # few-shot은 선택
    *few_shot_messages,
    {"role": "user", "content": user_input}
]
```

---

## 설치/버전 유의사항
- Gemma 3(`gemma3_text`) 아키텍처를 인식하려면 **Transformers 최신 버전**이 필요함.
  - 이 프로젝트에서는 `transformers==4.57.3`로 통일.
- CPU 전용 실행 시 예시:
```python
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

processor = AutoProcessor.from_pretrained(
    "google/functiongemma-270m-it",
    trust_remote_code=True
)
model = AutoModelForCausalLM.from_pretrained(
    "google/functiongemma-270m-it",
    torch_dtype=torch.float32,
    device_map="cpu",
    trust_remote_code=True
)
```

---

## 데모 테스트 케이스 (수동 확인)

### 단일 명령 (기기별 1개)
- "에어컨 꺼줘" → `ac_power_off`
- "TV 9번 채널로" → `tv_set_channel{channel:9}`
- "거실등 밝기 50%" → `light_set_brightness{brightness:50}`
- "주방 청소해줘" → `vacuum_clean_zone{zone:kitchen}`
- "오디오 꺼줘" → `audio_power_off`
- "커튼 반만 열어줘" → `curtain_set_position{position:50}`
- "환풍기 꺼줘" → `ventilation_power_off`

### 복합 명령 (2개)
- "TV 켜고 조명 꺼줘" → `tv_power_on` + `light_power_off`
- "로봇 청소기 끄고 환풍기 켜줘" → `vacuum_stop` + `ventilation_power_on`

### 복합 명령 (4개)
- "외출 준비해줘" → `light_power_off` + `tv_power_off` + `ac_power_off` + `ventilation_power_off`

> 문제 사례가 나오면 **키워드 규칙 대신** 함수 스키마 설명 보강 + few-shot 추가로 보완합니다.

## 구현 체크리스트
- [ ] developer 역할 메시지를 사용했는가
- [ ] tools(JSON schema)를 `apply_chat_template`에 전달했는가
- [ ] 출력 포맷(`<start_function_call>...`) 파싱 로직이 있는가
- [ ] 복수 함수 호출 파싱을 지원하는가 (멀티턴)
- [ ] `transformers>=4.57` 사용 중인가
- [ ] HF 로그인/라이선스 승인이 완료되었는가
- [ ] `.env`에 HF 토큰이 설정되었는가 (`HUGGINGFACE_HUB_TOKEN` 또는 `HF_TOKEN`)
- [ ] max_new_tokens를 충분히 설정했는가 (복합 명령: 256+)

---

## 참고 문서
- FunctionGemma 모델 카드 (HF): https://huggingface.co/google/functiongemma-270m-it
- FunctionGemma 개요 (Google AI): https://ai.google.dev/gemma/docs/functiongemma
- Full Function Calling Sequence: https://ai.google.dev/gemma/docs/functiongemma/full-function-calling-sequence-with-functiongemma
- Unsloth Multi-Turn Notebook: https://docs.unsloth.ai/models/functiongemma
- Gemma Cookbook (파인튜닝 예제): https://github.com/google-gemini/gemma-cookbook/blob/main/FunctionGemma/%5BFunctionGemma%5DFinetune_FunctionGemma_270M_for_Mobile_Actions_with_Hugging_Face.ipynb
- Mobile Actions 데이터셋: https://huggingface.co/datasets/google/mobile-actions
- Kaggle 모델 페이지: https://www.kaggle.com/models/google/functiongemma/
