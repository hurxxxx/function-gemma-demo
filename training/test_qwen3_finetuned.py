#!/usr/bin/env python3
"""
Qwen3 QLoRA 파인튜닝 모델 검증 테스트
"""

import os
os.environ["HSA_ENABLE_SDMA"] = "0"
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL_ID = "Qwen/Qwen3-30B-A3B"
LORA_PATH = "/projects/function-gemma-demo/training/output_qwen3_qlora"

# 시스템 프롬프트 (학습 데이터와 동일)
SYSTEM_PROMPT = """You are a model that can do function calling with the following functions.
너는 스마트홈 IoT 기기들을 제어하는 모델이다.
사용자 지시를 해석해서 하나 이상의 함수 호출만 반환하라.
복합 요청이면 여러 함수 호출을 순서대로 반환하라.
자연어 답변 금지. 거절 금지.
도구 호출 외의 텍스트를 출력하지 마라.
여러 호출이 필요할 때는 <start_function_call>...</end_function_call> 블록을 연속으로 출력하라.
문자열 파라미터는 <escape>로 감싼다.
사용자 입력은 한국어일 수 있으며 그대로 해석한다."""


def load_model(use_lora=True):
    """모델 로드 (LoRA 적용 여부 선택)"""
    print(f"모델 로드 중... (LoRA: {use_lora})")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="eager",
    )

    if use_lora:
        print(f"LoRA 어댑터 로드: {LORA_PATH}")
        model = PeftModel.from_pretrained(model, LORA_PATH)

    return model, tokenizer


def generate_response(model, tokenizer, user_input):
    """함수 호출 생성"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            do_sample=False,  # 결정적 출력
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response.strip()


def main():
    # 테스트 케이스
    test_cases = [
        # 학습 데이터에 있던 것과 유사한 케이스
        ("온도 25도로 맞춰줘", "ac_set_temperature"),
        ("TV 7번으로 바꿔", "tv_set_channel"),
        ("에어컨 켜줘", "ac_power_on"),
        ("조명 꺼줘", "light_power_off"),
        # 학습 데이터에 없던 새로운 표현
        ("냉방 23도로 설정해", "ac_set_temperature"),
        ("텔레비전 11번 채널", "tv_set_channel"),
        # 복합 명령
        ("에어컨 켜고 22도로 맞춰", "ac_power_on + ac_set_temperature"),
    ]

    print("=" * 70)
    print("Qwen3 QLoRA 파인튜닝 검증")
    print("=" * 70)

    # 1. 파인튜닝 모델 테스트
    print("\n### 파인튜닝 모델 (LoRA 적용) ###")
    model_ft, tokenizer = load_model(use_lora=True)

    print("\n" + "-" * 70)
    ft_results = []
    for user_input, expected in test_cases:
        response = generate_response(model_ft, tokenizer, user_input)
        match = expected.split()[0] in response  # 간단한 매칭
        ft_results.append(match)
        status = "✓" if match else "✗"
        print(f"{status} 입력: {user_input}")
        print(f"  예상: {expected}")
        print(f"  출력: {response[:100]}...")
        print()

    # 메모리 정리
    del model_ft
    torch.cuda.empty_cache()

    # 2. 원본 모델 테스트 (비교용)
    print("\n### 원본 모델 (LoRA 미적용) ###")
    model_base, tokenizer = load_model(use_lora=False)

    print("\n" + "-" * 70)
    base_results = []
    for user_input, expected in test_cases:
        response = generate_response(model_base, tokenizer, user_input)
        match = expected.split()[0] in response
        base_results.append(match)
        status = "✓" if match else "✗"
        print(f"{status} 입력: {user_input}")
        print(f"  예상: {expected}")
        print(f"  출력: {response[:100]}...")
        print()

    # 결과 요약
    print("=" * 70)
    print("결과 요약")
    print("=" * 70)
    print(f"파인튜닝 모델: {sum(ft_results)}/{len(ft_results)} 정답")
    print(f"원본 모델:     {sum(base_results)}/{len(base_results)} 정답")


if __name__ == "__main__":
    main()
