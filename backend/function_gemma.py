"""
FunctionGemma 모델 래퍼
자연어를 함수 호출로 변환 (홈 IoT 제어용)
"""
import re
import json
from typing import Optional
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

from home_controller import HOME_FUNCTION_SCHEMAS

BASE_SYSTEM_PROMPT_LINES = [
    "You are a model that can do function calling with the following functions.",
    "너는 스마트홈 IoT 기기들을 제어하는 모델이다.",
    "사용자 지시를 해석해서 하나 이상의 함수 호출만 반환하라.",
    "복합 요청이면 여러 함수 호출을 순서대로 반환하라.",
    "자연어 답변 금지. 거절 금지.",
    "도구 호출 외의 텍스트를 출력하지 마라.",
    "여러 호출이 필요할 때는 <start_function_call>...</end_function_call> 블록을 연속으로 출력하라.",
    "문자열 파라미터는 <escape>로 감싼다.",
    "사용자 입력은 한국어일 수 있으며 그대로 해석한다.",
]


class FunctionGemmaModel:
    """FunctionGemma 모델 래퍼"""

    def __init__(self, model_name: str = "google/functiongemma-270m-it"):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.allowed_functions = {
            schema["function"]["name"]
            for schema in HOME_FUNCTION_SCHEMAS
            if isinstance(schema, dict) and isinstance(schema.get("function"), dict)
        }
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
            dtype=torch.float32,  # CPU에서는 float32
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
        calls = self.parse_function_calls(output)
        return calls[0] if calls else None

    def parse_function_calls(self, output: str) -> list[dict]:
        calls: list[dict] = []

        segments = re.findall(
            r"<start_(?:of_)?function_call>(.*?)<end_(?:of_)?function_call>",
            output,
            flags=re.DOTALL,
        )
        for segment in segments:
            parsed = self._parse_function_segment(segment)
            if parsed:
                calls.append(parsed)

        if calls:
            return calls

        for name, params in re.findall(r"call:([a-zA-Z_]\w*)\{([^}]*)\}", output):
            calls.append({
                "function_name": name,
                "parameters": self._parse_parameters(params),
            })

        if calls:
            return calls

        for name, params in re.findall(r"call:([a-zA-Z_]\w*)\(([^)]*)\)", output):
            calls.append({
                "function_name": name,
                "parameters": self._parse_parameters(params),
            })

        if calls:
            return calls

        json_candidate = self._extract_json_blob(output)
        if json_candidate:
            parsed_json = self._parse_json_function_call(json_candidate)
            if parsed_json:
                return [parsed_json]

        return []

    def _extract_function_call_segment(self, output: str) -> Optional[str]:
        start_tokens = ("<start_function_call>", "<start_of_function_call>")
        end_tokens = ("<end_function_call>", "<end_of_function_call>")

        for start_token in start_tokens:
            start_index = output.find(start_token)
            if start_index == -1:
                continue

            search_from = start_index + len(start_token)
            for end_token in end_tokens:
                end_index = output.find(end_token, search_from)
                if end_index != -1:
                    return output[search_from:end_index].strip()

        return None

    def _parse_function_segment(self, segment: str) -> Optional[dict]:
        text = segment.strip()
        if text.startswith("call:"):
            text = text[len("call:"):].strip()

        if text.startswith("{"):
            parsed_json = self._parse_json_function_call(text)
            if parsed_json:
                return parsed_json

        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start == -1 or brace_end == -1 or brace_end <= brace_start:
            return None

        function_name = text[:brace_start].strip()
        params_str = text[brace_start + 1:brace_end].strip()

        if not function_name:
            return None

        return {
            "function_name": function_name,
            "parameters": self._parse_parameters(params_str)
        }

    def _parse_parameters(self, params_str: str) -> dict:
        if not params_str:
            return {}

        if "<escape>" in params_str:
            parameters = {}
            param_pattern = r"(\w+):<escape>([^<]*)<escape>"
            for key, value in re.findall(param_pattern, params_str):
                parameters[key] = self._coerce_value(value)
            return parameters

        # JSON 형태 파라미터 처리
        json_text = params_str
        if not (json_text.startswith("{") and json_text.endswith("}")):
            json_text = f"{{{json_text}}}"

        try:
            parsed = json.loads(json_text)
            if isinstance(parsed, dict):
                return {k: self._coerce_value(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            pass

        # key:value 형태 간단 파싱
        parameters = {}
        for chunk in params_str.split(","):
            if ":" not in chunk:
                continue
            key, value = chunk.split(":", 1)
            parameters[key.strip()] = self._coerce_value(value.strip())
        return parameters

    def _coerce_value(self, value):
        if not isinstance(value, str):
            return value

        cleaned = value.strip().strip('"').strip("'")
        lowered = cleaned.lower()

        if lowered in ("true", "false"):
            return lowered == "true"

        if cleaned.lstrip("+-").isdigit():
            return int(cleaned)

        if cleaned.replace(".", "", 1).lstrip("+-").isdigit():
            return float(cleaned)

        return cleaned

    def _parse_json_function_call(self, json_text: str) -> Optional[dict]:
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        if "function_call" in payload and isinstance(payload["function_call"], dict):
            payload = payload["function_call"]

        function_block = payload.get("function")
        if isinstance(function_block, dict):
            name = function_block.get("name")
            arguments = function_block.get("arguments", function_block.get("parameters", {}))
        else:
            name = payload.get("name") or payload.get("function_name")
            arguments = payload.get("arguments", payload.get("parameters", {}))

        if not name:
            return None

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        if not isinstance(arguments, dict):
            arguments = {}

        return {
            "function_name": name,
            "parameters": {k: self._coerce_value(v) for k, v in arguments.items()}
        }

    def _extract_json_blob(self, text: str) -> Optional[str]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start:end + 1]

    def _validate_function_call(self, function_call: Optional[dict]) -> Optional[dict]:
        if not function_call or not isinstance(function_call, dict):
            return None

        name = function_call.get("function_name")
        if not isinstance(name, str) or name not in self.allowed_functions:
            return None

        parameters = function_call.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        return {"function_name": name, "parameters": parameters}

    def _build_system_prompt(self, context: Optional[dict]) -> str:
        prompt_lines = list(BASE_SYSTEM_PROMPT_LINES)

        if context:
            prompt_lines.append("")
            prompt_lines.append("현재 기기 상태:")
            # 에어컨
            if "ac" in context:
                ac = context["ac"]
                power = "켜짐" if ac.get("power") else "꺼짐"
                prompt_lines.append(f"- 에어컨: {power}, {ac.get('temperature')}°C, 모드={ac.get('mode')}, 팬={ac.get('fan_speed')}")
            # TV
            if "tv" in context:
                tv = context["tv"]
                power = "켜짐" if tv.get("power") else "꺼짐"
                app = f", 앱={tv.get('current_app')}" if tv.get("current_app") else ""
                prompt_lines.append(f"- TV: {power}, 채널={tv.get('channel')}, 볼륨={tv.get('volume')}{app}")
            # 거실등
            if "light" in context:
                light = context["light"]
                power = "켜짐" if light.get("power") else "꺼짐"
                prompt_lines.append(f"- 거실등: {power}, 밝기={light.get('brightness')}%, 색온도={light.get('color_temp')}K")
            # 로봇청소기
            if "vacuum" in context:
                vacuum = context["vacuum"]
                zone = f", 구역={vacuum.get('current_zone')}" if vacuum.get("current_zone") else ""
                prompt_lines.append(f"- 로봇청소기: 상태={vacuum.get('status')}{zone}")
            # 오디오
            if "audio" in context:
                audio = context["audio"]
                power = "켜짐" if audio.get("power") else "꺼짐"
                playlist = f", 플레이리스트={audio.get('current_playlist')}" if audio.get("current_playlist") else ""
                prompt_lines.append(f"- 오디오: {power}, 볼륨={audio.get('volume')}, 재생={audio.get('playback')}{playlist}")
            # 전동커튼
            if "curtain" in context:
                curtain = context["curtain"]
                prompt_lines.append(f"- 전동커튼: 위치={curtain.get('position')}%")
            # 환풍기
            if "ventilation" in context:
                vent = context["ventilation"]
                power = "켜짐" if vent.get("power") else "꺼짐"
                prompt_lines.append(f"- 환풍기: {power}, 속도={vent.get('speed')}")

        return "\n".join(prompt_lines)

    def _build_few_shot_messages(self) -> list[dict]:
        return []

    def generate_function_call(self, user_input: str, context: Optional[dict] = None) -> dict:
        """
        사용자 입력을 함수 호출로 변환

        Returns:
            {
                "raw_output": str,
                "function_call": {"function_name": str, "parameters": dict} or None,
                "function_calls": [{"function_name": str, "parameters": dict}, ...],
                "success": bool
            }
        """
        if not self.loaded:
            self.load()

        normalized_input = user_input

        # 시스템 프롬프트 구성
        system_prompt = self._build_system_prompt(context)

        messages = [
            {
                "role": "developer",
                "content": system_prompt
            },
            *self._build_few_shot_messages(),
            {
                "role": "user",
                "content": normalized_input
            },
        ]

        # 입력 토크나이징
        try:
            inputs = self.processor.apply_chat_template(
                messages,
                tools=HOME_FUNCTION_SCHEMAS,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )
        except Exception:
            merged_prompt = f"{system_prompt}\n\nUser: {normalized_input}"
            inputs = self.processor.apply_chat_template(
                [{"role": "developer", "content": merged_prompt}],
                tools=HOME_FUNCTION_SCHEMAS,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )

        # 생성
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,  # 복합 명령을 위해 증가
                pad_token_id=self.processor.eos_token_id,
                do_sample=False
            )

        # 디코딩
        raw_output = self.processor.decode(
            outputs[0][len(inputs["input_ids"][0]):],
            skip_special_tokens=False
        )

        # 함수 호출 파싱
        function_calls = []
        for call in self.parse_function_calls(raw_output):
            validated = self._validate_function_call(call)
            if validated:
                function_calls.append(validated)

        function_call = function_calls[0] if function_calls else None

        return {
            "raw_output": raw_output,
            "function_call": function_call,
            "function_calls": function_calls,
            "success": bool(function_calls)
        }


# 전역 모델 인스턴스 (싱글톤)
_model_instance: Optional[FunctionGemmaModel] = None


def get_model() -> FunctionGemmaModel:
    """모델 인스턴스 가져오기 (싱글톤)"""
    global _model_instance
    if _model_instance is None:
        _model_instance = FunctionGemmaModel()
    return _model_instance
