"""
FunctionGemma 모델 래퍼
자연어를 함수 호출로 변환
"""
import re
import json
from typing import Optional
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

from ac_controller import AC_FUNCTION_SCHEMAS


class FunctionGemmaModel:
    """FunctionGemma 모델 래퍼"""

    def __init__(self, model_name: str = "google/functiongemma-270m-it"):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.loaded = False

    def load(self):
        """모델 로드 (지연 로딩)"""
        if self.loaded:
            return

        print(f"Loading FunctionGemma model: {self.model_name}")

        # CPU에서 실행, 메모리 최적화
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,  # CPU에서는 float32
            device_map="cpu",
            trust_remote_code=True
        )

        self.loaded = True
        print("FunctionGemma model loaded successfully!")

    def parse_function_call(self, output: str) -> Optional[dict]:
        """
        모델 출력에서 함수 호출 파싱

        FunctionGemma 출력 형식:
        <start_function_call>call:function_name{param:<escape>value<escape>}<end_function_call>
        """
        # 함수 호출 패턴 매칭
        pattern = r"<start_function_call>call:(\w+)\{([^}]*)\}<end_function_call>"
        match = re.search(pattern, output)

        if not match:
            # 간단한 형식도 시도: call:function_name{...}
            pattern2 = r"call:(\w+)\{([^}]*)\}"
            match = re.search(pattern2, output)

        if not match:
            return None

        function_name = match.group(1)
        params_str = match.group(2)

        # 파라미터 파싱: key:<escape>value<escape>
        parameters = {}
        if params_str:
            param_pattern = r"(\w+):<escape>([^<]*)<escape>"
            param_matches = re.findall(param_pattern, params_str)
            for key, value in param_matches:
                # 숫자 변환 시도
                try:
                    if value.lstrip('-').isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).lstrip('-').isdigit():
                        value = float(value)
                except:
                    pass
                parameters[key] = value

        return {
            "function_name": function_name,
            "parameters": parameters
        }

    def generate_function_call(self, user_input: str) -> dict:
        """
        사용자 입력을 함수 호출로 변환

        Returns:
            {
                "raw_output": str,
                "function_call": {"function_name": str, "parameters": dict} or None,
                "success": bool
            }
        """
        if not self.loaded:
            self.load()

        # 시스템 프롬프트 구성
        system_prompt = """You are a car air conditioner controller.
Understand user intent from natural language and call appropriate standard API.

Available standard APIs:
- get_current_temperature(): Get current temperature
- set_temperature(temperature): Set temperature (16-30°C)
- adjust_temperature(delta): Change temperature by delta amount
- set_fan_speed(speed): low/medium/high/auto
- set_mode(mode): cooling/heating/auto/ventilation
- power_on() / power_off()

Understand user intent and decide appropriate action:
- If user feels hot/warm -> lower temperature
- If user feels cold -> raise temperature
- If user wants comfortable/optimal temp -> set reasonable temperature
- If user wants stronger/weaker airflow -> adjust fan speed
- Determine appropriate values based on context

Call the standard API with values you determine are appropriate."""

        messages = [
            {
                "role": "developer",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        # 입력 토크나이징
        inputs = self.processor.apply_chat_template(
            messages,
            tools=AC_FUNCTION_SCHEMAS,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        )

        # 생성
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=128,
                pad_token_id=self.processor.eos_token_id,
                do_sample=False
            )

        # 디코딩
        raw_output = self.processor.decode(
            outputs[0][len(inputs["input_ids"][0]):],
            skip_special_tokens=False
        )

        # 함수 호출 파싱
        function_call = self.parse_function_call(raw_output)

        return {
            "raw_output": raw_output,
            "function_call": function_call,
            "success": function_call is not None
        }


# 전역 모델 인스턴스 (싱글톤)
_model_instance: Optional[FunctionGemmaModel] = None


def get_model() -> FunctionGemmaModel:
    """모델 인스턴스 가져오기 (싱글톤)"""
    global _model_instance
    if _model_instance is None:
        _model_instance = FunctionGemmaModel()
    return _model_instance
