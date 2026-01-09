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
from translation import get_translator


class FunctionGemmaModel:
    """FunctionGemma 모델 래퍼"""

    def __init__(self, model_name: str = "google/functiongemma-270m-it"):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.translator = get_translator()
        self.allowed_functions = {
            schema["function"]["name"]
            for schema in AC_FUNCTION_SCHEMAS
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
        segment = self._extract_function_call_segment(output)
        if segment:
            parsed = self._parse_function_segment(segment)
            if parsed:
                return parsed

        # 간단한 형식도 시도: call:function_name{...}
        match = re.search(r"call:([a-zA-Z_]\w*)\{([^}]*)\}", output)
        if match:
            return {
                "function_name": match.group(1),
                "parameters": self._parse_parameters(match.group(2))
            }

        # 괄호 형식도 시도: call:function_name(...)
        match = re.search(r"call:([a-zA-Z_]\w*)\(([^)]*)\)", output)
        if match:
            return {
                "function_name": match.group(1),
                "parameters": self._parse_parameters(match.group(2))
            }

        # JSON 형태 함수 호출 시도
        json_candidate = self._extract_json_blob(output)
        if json_candidate:
            parsed_json = self._parse_json_function_call(json_candidate)
            if parsed_json:
                return parsed_json

        return None

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

    def _clamp_temperature(self, value: int) -> int:
        return max(16, min(30, value))

    def _apply_overrides(
        self,
        user_input: str,
        function_call: Optional[dict],
        context: Optional[dict]
    ) -> Optional[dict]:
        validated = self._validate_function_call(function_call)
        if validated:
            if validated.get("function_name") == "set_temperature":
                temperature = validated.get("parameters", {}).get("temperature")
                if isinstance(temperature, (int, float)):
                    validated["parameters"]["temperature"] = self._clamp_temperature(int(temperature))
            return validated
        return None

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
        prompt_lines = [
            "You are a car air conditioner controller.",
            "Interpret user intent from natural language and return exactly one tool call.",
            "Do not answer in natural language. Do not refuse. Always call one of the provided tools.",
            "Use the available APIs and determine appropriate values.",
            "The user message is provided in English (translated if needed).",
            "",
            "IMPORTANT: Numbers are in Celsius.",
            "- Use set_temperature ONLY for explicit target requests (e.g., 'Set to 24').",
            "- 'Three more degrees' or 'N more degrees' means INCREASE temperature: adjust_temperature with delta=+N",
            "- 'Lower by 2' or 'N degrees less' means DECREASE temperature: adjust_temperature with delta=-N",
            "- Do NOT use set_temperature for relative requests like 'increase/decrease/raise/lower'.",
            "- When user says 'more' or 'additional', always use positive delta (increase)",
            "- When user says 'less' or 'lower', always use negative delta (decrease)"
        ]

        if context:
            prompt_lines.append("")
            prompt_lines.append("Current context:")
            context_lines = [
                ("Power", "power", ""),
                ("Target temperature", "temperature", "°C"),
                ("Indoor temperature", "indoor_temperature", "°C"),
                ("Outdoor temperature", "outdoor_temperature", "°C"),
                ("Mode", "mode", ""),
                ("Fan speed", "fan_speed", "")
            ]
            for label, key, unit in context_lines:
                value = context.get(key)
                if value is None:
                    continue
                if key == "power":
                    value = "on" if value else "off"
                prompt_lines.append(f"- {label}: {value}{unit}")

        prompt_lines.extend([
            "",
            "Guidelines:",
            "- If the user asks for the current temperature (e.g., 'current temperature', 'what's the temperature now'), use get_current_temperature().",
            "- Do NOT change settings for current temperature questions.",
            "- Use set_temperature for explicit targets, adjust_temperature for relative changes.",
            "- If the user feels hot/warm or mentions sweating/stuffy air, lower the target by 1-3°C.",
            "- If the user feels cold or mentions shivering, raise the target by 1-3°C.",
            "- For comfortable/optimal, use 24-26°C when outdoor >= 26°C, 26-28°C when outdoor <= 15°C, otherwise 24-25°C.",
            "- Keep temperature within 16-30°C.",
            "- If airflow strength is requested, use set_fan_speed(low/medium/high/auto).",
            "- Map strong/max -> high, weak/low -> low, medium/normal -> medium, auto/automatic -> auto.",
            "- If the input is only about airflow, do not change temperature or mode.",
            "- If a mode is requested, use set_mode(cooling/heating/auto/ventilation).",
            "- If power on/off is requested, use power_on() or power_off().",
            "- Treat implicit statements (e.g., 'It's hot', 'Kids are sweating') as requests to adjust the AC.",
            "",
            "Examples:",
            "User: Make the fan stronger",
            "Tool call: <start_function_call>call:set_fan_speed{speed:<escape>high<escape>}<end_function_call>",
            "User: Increase the temperature by 2 degrees",
            "Tool call: <start_function_call>call:adjust_temperature{delta:<escape>2<escape>}<end_function_call>",
            "User: Lower the temperature by 1 degree",
            "Tool call: <start_function_call>call:adjust_temperature{delta:<escape>-1<escape>}<end_function_call>",
            "User: Set the temperature to 23 degrees",
            "Tool call: <start_function_call>call:set_temperature{temperature:<escape>23<escape>}<end_function_call>",
            "User: What's the current temperature?",
            "Tool call: <start_function_call>call:get_current_temperature{}<end_function_call>",
            "User: Make the fan weaker",
            "Tool call: <start_function_call>call:set_fan_speed{speed:<escape>low<escape>}<end_function_call>",
            "User: Fan to auto",
            "Tool call: <start_function_call>call:set_fan_speed{speed:<escape>auto<escape>}<end_function_call>",
            "User: Medium fan speed",
            "Tool call: <start_function_call>call:set_fan_speed{speed:<escape>medium<escape>}<end_function_call>",
            "Return only the tool call."
        ])

        return "\n".join(prompt_lines)

    def _build_few_shot_messages(self) -> list[dict]:
        return [
            {
                "role": "user",
                "content": "Set the temperature to 23 degrees"
            },
            {
                "role": "assistant",
                "content": "<start_function_call>call:set_temperature{temperature:<escape>23<escape>}<end_function_call>"
            },
            {
                "role": "user",
                "content": "Set the temperature to 26 degrees"
            },
            {
                "role": "assistant",
                "content": "<start_function_call>call:set_temperature{temperature:<escape>26<escape>}<end_function_call>"
            },
            {
                "role": "user",
                "content": "Increase the temperature by 2 degrees"
            },
            {
                "role": "assistant",
                "content": "<start_function_call>call:adjust_temperature{delta:<escape>2<escape>}<end_function_call>"
            },
            {
                "role": "user",
                "content": "Lower the temperature by 1 degree"
            },
            {
                "role": "assistant",
                "content": "<start_function_call>call:adjust_temperature{delta:<escape>-1<escape>}<end_function_call>"
            },
            {
                "role": "user",
                "content": "What's the current temperature?"
            },
            {
                "role": "assistant",
                "content": "<start_function_call>call:get_current_temperature{}<end_function_call>"
            },
        ]

    def generate_function_call(self, user_input: str, context: Optional[dict] = None) -> dict:
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

        normalized_input = user_input
        if self.translator:
            translated_input, _translation_info = self.translator.translate(user_input)
            if translated_input:
                normalized_input = translated_input

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
                tools=AC_FUNCTION_SCHEMAS,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )
        except Exception:
            merged_prompt = f"{system_prompt}\n\nUser: {normalized_input}"
            inputs = self.processor.apply_chat_template(
                [{"role": "developer", "content": merged_prompt}],
                tools=AC_FUNCTION_SCHEMAS,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )

        # 생성
        with torch.inference_mode():
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
        function_call = self._apply_overrides(normalized_input, function_call, context)

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
