#!/usr/bin/env python3
"""
Qwen3-30B-A3B 4bit 양자화 추론 테스트
ROCm gfx1151 (Ryzen AI Max+ 395) 환경
"""

import os
os.environ["HSA_ENABLE_SDMA"] = "0"
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen3-30B-A3B"

def main():
    print("=" * 60)
    print("Qwen3-30B-A3B 4bit 추론 테스트")
    print("=" * 60)

    print(f"\nPyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device: {torch.cuda.get_device_name(0)}")
        print(f"Memory: {torch.cuda.get_device_properties(0).total_memory // 1024**3} GB")

    # 4bit 양자화 설정
    print("\n[1/3] BitsAndBytesConfig 설정...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # 토크나이저 로드
    print("\n[2/3] 토크나이저 로드...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    # 모델 로드
    print("\n[3/3] 모델 로드 (4bit 양자화)...")
    print("(첫 실행 시 모델 다운로드에 시간이 걸립니다)")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="eager",  # gfx1151 필수
    )

    print(f"\n모델 로드 완료!")
    print(f"모델 메모리: {model.get_memory_footprint() / 1024**3:.2f} GB")

    # 테스트 질문들
    test_questions = [
        "안녕하세요, 자기소개 해주세요.",
        "Python에서 리스트와 튜플의 차이점은 무엇인가요?",
        "한국의 수도는 어디인가요?",
    ]

    print("\n" + "=" * 60)
    print("추론 테스트")
    print("=" * 60)

    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 질문 {i}: {question}")

        messages = [{"role": "user", "content": question}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # 응답에서 질문 부분 제거
        if question in response:
            response = response.split(question)[-1].strip()

        print(f"--- 응답:\n{response[:500]}...")  # 처음 500자만 출력

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
