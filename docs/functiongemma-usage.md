# FunctionGemma Usage Notes

Korean: [functiongemma-usage.ko.md](functiongemma-usage.ko.md)

Source: https://huggingface.co/google/functiongemma-270m-it

## Key Points
- FunctionGemma is a **function-calling model**, not a general chat model.
- **Domain/task-specific fine-tuning is recommended**, especially for multi-turn use.
- Gemma 3-based architecture with a **FunctionGemma-specific chat format**.
- **Developer role message is required** to enable function-calling mode.
- Output uses **function call tokens**:
  - `<start_function_call>call:func{param:<escape>value<escape>}<end_function_call>`
- Max context: 32K tokens.
- **Gated model**: requires HF login/license acceptance.
  - Set `HUGGINGFACE_HUB_TOKEN` or `HF_TOKEN` in `.env` for training/inference.

---

## Multi-Turn Function Calling

### Official multi-turn flow
```
[Turn 1] developer: system prompt + tool schema
[Turn 2] user: "TV 켜고 조명 꺼줘"
[Turn 3] assistant: <start_function_call>call:tv_power_on{}<end_function_call>
                    <start_function_call>call:light_power_off{}<end_function_call>
[Turn 4] tool: [
    {"name": "tv_power_on", "response": {"success": true}},
    {"name": "light_power_off", "response": {"success": true}}
]
[Turn 5] assistant: "TV를 켜고 조명을 껐습니다."
```

### Role definitions
| Role | Description |
|------|-------------|
| `developer` | System prompt, enables function-calling mode (required) |
| `user` | User voice/text command |
| `assistant` | Model output with function calls |
| `tool` | Function execution results (multiple allowed) |

### Multiple calls in one response
```
<start_function_call>call:function1{}<end_function_call>
<start_function_call>call:function2{param:<escape>value<escape>}<end_function_call>
```

### Feeding tool results back
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

## Multilingual Input (Project Setting)
- The project sends **Korean input directly** to FunctionGemma.
- **No rules/keyword-based post-processing** is used.
- For better accuracy in Korean, **LoRA fine-tuning is recommended**.
- Fine-tuning guide: docs/functiongemma-finetune.md

---

## Required Usage Pattern

### 1) Define tools (JSON schema)
```python
function_schema = {
    "type": "function",
    "function": {
        "name": "tv_power_on",
        "description": "Turns on the TV.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}
```

### 2) Provide developer message
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

### 3) Generate and decode
```python
out = model.generate(
    **inputs.to(model.device),
    pad_token_id=processor.eos_token_id,
    max_new_tokens=256
)
output = processor.decode(out[0][len(inputs["input_ids"][0]):], skip_special_tokens=False)
# <start_function_call>call:tv_power_on{}<end_function_call>
```

### 4) Parse function calls
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
    params = {}
    for key, value in re.findall(r"(\w+):<escape>([^<]*)<escape>", params_str):
        params[key] = coerce_value(value)
    return params
```

---

## Few-Shot Examples (Optional)
This project **does not use runtime few-shot** and relies on fine-tuning.
Use few-shot only for format validation or quick prototyping.

```python
few_shot_messages = [
    {"role": "user", "content": "에어컨 켜줘"},
    {"role": "assistant", "content": "<start_function_call>call:ac_power_on{}<end_function_call>"},
    {"role": "user", "content": "TV 9번 채널로"},
    {"role": "assistant", "content": "<start_function_call>call:tv_set_channel{channel:<escape>9<escape>}<end_function_call>"},
]

messages = [
    {"role": "developer", "content": system_prompt},
    *few_shot_messages,
    {"role": "user", "content": user_input}
]
```

---

## Version Notes
- Transformers must be recent for Gemma 3 (`gemma3_text`).
- This project pins `transformers==4.57.3`.

CPU-only example:
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

## Demo Test Cases (Manual)

### Single device
- "에어컨 꺼줘" -> `ac_power_off`
- "TV 9번 채널로" -> `tv_set_channel{channel:9}`
- "거실등 밝기 50%" -> `light_set_brightness{brightness:50}`
- "주방 청소해줘" -> `vacuum_clean_zone{zone:kitchen}`
- "오디오 꺼줘" -> `audio_power_off`
- "커튼 반만 열어줘" -> `curtain_set_position{position:50}`
- "환풍기 꺼줘" -> `ventilation_power_off`

### Two-device
- "TV 켜고 조명 꺼줘" -> `tv_power_on` + `light_power_off`
- "로봇 청소기 끄고 환풍기 켜줘" -> `vacuum_stop` + `ventilation_power_on`

### Four-device
- "외출 준비해줘" -> `light_power_off` + `tv_power_off` + `ac_power_off` + `ventilation_power_off`

## Related
- functiongemma-finetune.md
- fine-tuning.md
- functiongemma-test-report.md
- demo-commands.md
