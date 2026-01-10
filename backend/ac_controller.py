"""
에어컨 상태 관리 및 제어 함수들
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any
import json


class FanSpeed(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AUTO = "auto"


class ACMode(str, Enum):
    COOLING = "cooling"
    HEATING = "heating"
    AUTO = "auto"
    VENTILATION = "ventilation"


@dataclass
class ACState:
    """에어컨 상태"""
    power: bool = False
    temperature: int = 24  # 16-30
    indoor_temperature: int = 26  # 실내 온도
    outdoor_temperature: int = 32  # 외기 온도
    fan_speed: FanSpeed = FanSpeed.AUTO
    mode: ACMode = ACMode.COOLING

    def to_dict(self) -> dict:
        return {
            "power": self.power,
            "temperature": self.temperature,
            "indoor_temperature": self.indoor_temperature,
            "outdoor_temperature": self.outdoor_temperature,
            "fan_speed": self.fan_speed.value,
            "mode": self.mode.value
        }


class ACController:
    """에어컨 컨트롤러 - 상태 관리 및 함수 실행"""

    MIN_TEMP = 16
    MAX_TEMP = 30
    MIN_ENV_TEMP = -20
    MAX_ENV_TEMP = 50

    def __init__(self, on_state_change: Callable[[dict], Any] = None):
        self.state = ACState()
        self.on_state_change = on_state_change

    def _notify_change(self):
        """상태 변경 알림"""
        if self.on_state_change:
            self.on_state_change(self.state.to_dict())

    def get_current_temperature(self) -> dict:
        """현재 설정된 온도 조회"""
        return {
            "temperature": self.state.temperature,
            "indoor_temperature": self.state.indoor_temperature,
            "outdoor_temperature": self.state.outdoor_temperature,
            "power": self.state.power
        }

    def set_temperature(self, temperature: int) -> dict:
        """온도 설정 (16-30도)"""
        if temperature < self.MIN_TEMP:
            temperature = self.MIN_TEMP
        elif temperature > self.MAX_TEMP:
            temperature = self.MAX_TEMP

        old_temp = self.state.temperature
        self.state.temperature = temperature

        # 전원이 꺼져있으면 자동으로 켜기
        if not self.state.power:
            self.state.power = True

        self._notify_change()
        return {
            "success": True,
            "previous_temperature": old_temp,
            "current_temperature": self.state.temperature,
            "message": f"온도를 {self.state.temperature}도로 설정했습니다."
        }

    def adjust_temperature(self, delta: int) -> dict:
        """온도 증감 (delta만큼 조절)"""
        new_temp = self.state.temperature + delta
        return self.set_temperature(new_temp)

    def set_fan_speed(self, speed: str) -> dict:
        """팬 속도 설정"""
        try:
            self.state.fan_speed = FanSpeed(speed.lower())

            if not self.state.power:
                self.state.power = True

            self._notify_change()
            return {
                "success": True,
                "fan_speed": self.state.fan_speed.value,
                "message": f"팬 속도를 {self.state.fan_speed.value}로 설정했습니다."
            }
        except ValueError:
            return {
                "success": False,
                "message": f"잘못된 팬 속도입니다. low, medium, high, auto 중 선택하세요."
            }

    def set_mode(self, mode: str) -> dict:
        """에어컨 모드 설정"""
        try:
            self.state.mode = ACMode(mode.lower())

            if not self.state.power:
                self.state.power = True

            self._notify_change()
            return {
                "success": True,
                "mode": self.state.mode.value,
                "message": f"모드를 {self.state.mode.value}로 설정했습니다."
            }
        except ValueError:
            return {
                "success": False,
                "message": f"잘못된 모드입니다. cooling, heating, auto, ventilation 중 선택하세요."
            }

    def power_on(self) -> dict:
        """에어컨 켜기"""
        self.state.power = True
        self._notify_change()
        return {
            "success": True,
            "power": True,
            "message": "에어컨을 켰습니다."
        }

    def power_off(self) -> dict:
        """에어컨 끄기"""
        self.state.power = False
        self._notify_change()
        return {
            "success": True,
            "power": False,
            "message": "에어컨을 껐습니다."
        }

    def update_environment(
        self,
        indoor_temperature: int | None = None,
        outdoor_temperature: int | None = None
    ) -> dict:
        """실내/외기 온도 업데이트"""
        updated = False

        if indoor_temperature is not None:
            self.state.indoor_temperature = self._clamp_environment_temperature(indoor_temperature)
            updated = True

        if outdoor_temperature is not None:
            self.state.outdoor_temperature = self._clamp_environment_temperature(outdoor_temperature)
            updated = True

        if updated:
            self._notify_change()

        return {
            "success": updated,
            "indoor_temperature": self.state.indoor_temperature,
            "outdoor_temperature": self.state.outdoor_temperature
        }

    def _clamp_environment_temperature(self, temperature: int) -> int:
        return max(self.MIN_ENV_TEMP, min(self.MAX_ENV_TEMP, temperature))

    def execute_function(self, function_name: str, parameters: dict = None) -> dict:
        """함수 이름과 파라미터로 함수 실행"""
        parameters = parameters or {}

        function_map = {
            "get_current_temperature": self.get_current_temperature,
            "set_temperature": lambda: self.set_temperature(int(parameters.get("temperature", 24))),
            "adjust_temperature": lambda: self.adjust_temperature(int(parameters.get("delta", 0))),
            "set_fan_speed": lambda: self.set_fan_speed(parameters.get("speed", "auto")),
            "set_mode": lambda: self.set_mode(parameters.get("mode", "cooling")),
            "power_on": self.power_on,
            "power_off": self.power_off,
        }

        if function_name in function_map:
            return function_map[function_name]()
        else:
            return {"success": False, "message": f"알 수 없는 함수: {function_name}"}


# FunctionGemma용 함수 스키마 정의
AC_FUNCTION_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_temperature",
            "description": "현재 설정 온도와 실내/외기 온도를 조회합니다. (Get current target/indoor/outdoor temperatures)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_temperature",
            "description": "목표 온도를 설정합니다. (섭씨 16-30도)",
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {
                        "type": "integer",
                        "description": "목표 온도 (섭씨 16-30)"
                    }
                },
                "required": ["temperature"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_temperature",
            "description": "온도를 상대값으로 조절합니다. 양수는 올림, 음수는 내림.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta": {
                        "type": "integer",
                        "description": "온도 변화값 (양수: 올림, 음수: 내림)"
                    }
                },
                "required": ["delta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_fan_speed",
            "description": "팬 속도를 설정합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "auto"],
                        "description": "팬 속도 (low/medium/high/auto)"
                    }
                },
                "required": ["speed"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_mode",
            "description": "에어컨 모드를 설정합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["cooling", "heating", "auto", "ventilation"],
                        "description": "모드 (cooling/heating/auto/ventilation)"
                    }
                },
                "required": ["mode"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "power_on",
            "description": "에어컨 전원을 켭니다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "power_off",
            "description": "에어컨 전원을 끕니다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
