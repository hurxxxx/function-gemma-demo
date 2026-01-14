"""
홈 IoT 기기 상태 관리 및 제어 함수들
7개 기기: 에어컨, TV, 거실등, 로봇청소기, 오디오, 전동커튼, 환풍기
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


# === Enums ===

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


class VacuumStatus(str, Enum):
    IDLE = "idle"
    CLEANING = "cleaning"
    PAUSED = "paused"
    RETURNING = "returning"


class CleaningZone(str, Enum):
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"


class PlaybackStatus(str, Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


class CurtainStatus(str, Enum):
    OPENING = "opening"
    CLOSING = "closing"
    STOPPED = "stopped"


# === Device State Dataclasses ===

@dataclass
class ACState:
    """에어컨 상태"""
    power: bool = False
    temperature: int = 24  # 16-30
    mode: ACMode = ACMode.COOLING
    fan_speed: FanSpeed = FanSpeed.AUTO

    def to_dict(self) -> dict:
        return {
            "power": self.power,
            "temperature": self.temperature,
            "mode": self.mode.value,
            "fan_speed": self.fan_speed.value
        }


@dataclass
class TVState:
    """TV 상태"""
    power: bool = False
    channel: int = 1  # 1-100
    volume: int = 30  # 0-100
    current_app: str | None = None  # Netflix, YouTube, etc.

    def to_dict(self) -> dict:
        return {
            "power": self.power,
            "channel": self.channel,
            "volume": self.volume,
            "current_app": self.current_app
        }


@dataclass
class LightState:
    """거실등 상태"""
    power: bool = False
    brightness: int = 100  # 0-100%
    color_temp: int = 4000  # 2700-6500K (warm to cool)

    def to_dict(self) -> dict:
        return {
            "power": self.power,
            "brightness": self.brightness,
            "color_temp": self.color_temp
        }


@dataclass
class VacuumState:
    """로봇청소기 상태"""
    power: bool = False
    status: VacuumStatus = VacuumStatus.IDLE
    current_zone: str | None = None

    def to_dict(self) -> dict:
        return {
            "power": self.power,
            "status": self.status.value,
            "current_zone": self.current_zone
        }


@dataclass
class AudioState:
    """오디오 상태"""
    power: bool = False
    volume: int = 30  # 0-100
    playback: PlaybackStatus = PlaybackStatus.STOPPED
    current_playlist: str | None = None

    def to_dict(self) -> dict:
        return {
            "power": self.power,
            "volume": self.volume,
            "playback": self.playback.value,
            "current_playlist": self.current_playlist
        }


@dataclass
class CurtainState:
    """전동커튼 상태"""
    position: int = 100  # 0-100% (0=closed, 100=open)
    status: CurtainStatus = CurtainStatus.STOPPED

    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "status": self.status.value
        }


@dataclass
class VentilationState:
    """환풍기 상태"""
    power: bool = False
    speed: FanSpeed = FanSpeed.AUTO

    def to_dict(self) -> dict:
        return {
            "power": self.power,
            "speed": self.speed.value
        }


@dataclass
class HomeState:
    """전체 홈 상태"""
    ac: ACState = field(default_factory=ACState)
    tv: TVState = field(default_factory=TVState)
    light: LightState = field(default_factory=LightState)
    vacuum: VacuumState = field(default_factory=VacuumState)
    audio: AudioState = field(default_factory=AudioState)
    curtain: CurtainState = field(default_factory=CurtainState)
    ventilation: VentilationState = field(default_factory=VentilationState)

    def to_dict(self) -> dict:
        return {
            "ac": self.ac.to_dict(),
            "tv": self.tv.to_dict(),
            "light": self.light.to_dict(),
            "vacuum": self.vacuum.to_dict(),
            "audio": self.audio.to_dict(),
            "curtain": self.curtain.to_dict(),
            "ventilation": self.ventilation.to_dict()
        }


# === Home Controller ===

class HomeController:
    """홈 IoT 컨트롤러 - 7개 기기 상태 관리 및 함수 실행"""

    # 온도 범위
    AC_MIN_TEMP = 16
    AC_MAX_TEMP = 30

    # 볼륨 범위
    MIN_VOLUME = 0
    MAX_VOLUME = 100

    # TV 채널 범위
    MIN_CHANNEL = 1
    MAX_CHANNEL = 100

    # 밝기 범위
    MIN_BRIGHTNESS = 0
    MAX_BRIGHTNESS = 100

    # 색온도 범위
    MIN_COLOR_TEMP = 2700
    MAX_COLOR_TEMP = 6500

    # 커튼 위치 범위
    MIN_POSITION = 0
    MAX_POSITION = 100

    def __init__(self, on_state_change: Callable[[dict], Any] = None):
        self.state = HomeState()
        self.on_state_change = on_state_change

    def _notify_change(self):
        """상태 변경 알림"""
        if self.on_state_change:
            self.on_state_change(self.state.to_dict())

    # === 에어컨 함수들 ===

    def ac_power_on(self) -> dict:
        """에어컨 켜기"""
        self.state.ac.power = True
        self._notify_change()
        return {"success": True, "message": "에어컨을 켰습니다."}

    def ac_power_off(self) -> dict:
        """에어컨 끄기"""
        self.state.ac.power = False
        self._notify_change()
        return {"success": True, "message": "에어컨을 껐습니다."}

    def ac_set_temperature(self, temperature: int) -> dict:
        """에어컨 온도 설정 (16-30도)"""
        temperature = max(self.AC_MIN_TEMP, min(self.AC_MAX_TEMP, temperature))
        old_temp = self.state.ac.temperature
        self.state.ac.temperature = temperature
        if not self.state.ac.power:
            self.state.ac.power = True
        self._notify_change()
        return {
            "success": True,
            "previous_temperature": old_temp,
            "current_temperature": temperature,
            "message": f"에어컨 온도를 {temperature}도로 설정했습니다."
        }

    def ac_adjust_temperature(self, delta: int) -> dict:
        """에어컨 온도 증감"""
        new_temp = self.state.ac.temperature + delta
        return self.ac_set_temperature(new_temp)

    def ac_set_mode(self, mode: str) -> dict:
        """에어컨 모드 설정"""
        try:
            self.state.ac.mode = ACMode(mode.lower())
            if not self.state.ac.power:
                self.state.ac.power = True
            self._notify_change()
            return {"success": True, "mode": mode, "message": f"에어컨 모드를 {mode}로 설정했습니다."}
        except ValueError:
            return {"success": False, "message": "잘못된 모드입니다."}

    def ac_set_fan_speed(self, speed: str) -> dict:
        """에어컨 팬 속도 설정"""
        try:
            self.state.ac.fan_speed = FanSpeed(speed.lower())
            if not self.state.ac.power:
                self.state.ac.power = True
            self._notify_change()
            return {"success": True, "fan_speed": speed, "message": f"에어컨 팬 속도를 {speed}로 설정했습니다."}
        except ValueError:
            return {"success": False, "message": "잘못된 팬 속도입니다."}

    # === TV 함수들 ===

    def tv_power_on(self) -> dict:
        """TV 켜기"""
        self.state.tv.power = True
        self._notify_change()
        return {"success": True, "message": "TV를 켰습니다."}

    def tv_power_off(self) -> dict:
        """TV 끄기"""
        self.state.tv.power = False
        self.state.tv.current_app = None
        self._notify_change()
        return {"success": True, "message": "TV를 껐습니다."}

    def tv_set_channel(self, channel: int) -> dict:
        """TV 채널 설정 (1-100)"""
        channel = max(self.MIN_CHANNEL, min(self.MAX_CHANNEL, channel))
        self.state.tv.channel = channel
        self.state.tv.current_app = None  # 채널 변경 시 앱 종료
        if not self.state.tv.power:
            self.state.tv.power = True
        self._notify_change()
        return {"success": True, "channel": channel, "message": f"TV 채널을 {channel}번으로 변경했습니다."}

    def tv_set_volume(self, volume: int) -> dict:
        """TV 볼륨 설정 (0-100)"""
        volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, volume))
        self.state.tv.volume = volume
        if not self.state.tv.power:
            self.state.tv.power = True
        self._notify_change()
        return {"success": True, "volume": volume, "message": f"TV 볼륨을 {volume}으로 설정했습니다."}

    def tv_adjust_volume(self, delta: int) -> dict:
        """TV 볼륨 증감"""
        new_volume = self.state.tv.volume + delta
        return self.tv_set_volume(new_volume)

    def tv_launch_app(self, app_name: str) -> dict:
        """TV 앱 실행"""
        self.state.tv.current_app = app_name
        if not self.state.tv.power:
            self.state.tv.power = True
        self._notify_change()
        return {"success": True, "app": app_name, "message": f"{app_name}을(를) 실행했습니다."}

    # === 거실등 함수들 ===

    def light_power_on(self) -> dict:
        """거실등 켜기"""
        self.state.light.power = True
        self._notify_change()
        return {"success": True, "message": "거실등을 켰습니다."}

    def light_power_off(self) -> dict:
        """거실등 끄기"""
        self.state.light.power = False
        self._notify_change()
        return {"success": True, "message": "거실등을 껐습니다."}

    def light_set_brightness(self, brightness: int) -> dict:
        """거실등 밝기 설정 (0-100%)"""
        brightness = max(self.MIN_BRIGHTNESS, min(self.MAX_BRIGHTNESS, brightness))
        self.state.light.brightness = brightness
        if not self.state.light.power:
            self.state.light.power = True
        self._notify_change()
        return {"success": True, "brightness": brightness, "message": f"거실등 밝기를 {brightness}%로 설정했습니다."}

    def light_adjust_brightness(self, delta: int) -> dict:
        """거실등 밝기 증감"""
        new_brightness = self.state.light.brightness + delta
        return self.light_set_brightness(new_brightness)

    def light_set_color_temp(self, temp: int) -> dict:
        """거실등 색온도 설정 (2700K-6500K)"""
        temp = max(self.MIN_COLOR_TEMP, min(self.MAX_COLOR_TEMP, temp))
        self.state.light.color_temp = temp
        if not self.state.light.power:
            self.state.light.power = True
        self._notify_change()
        warmth = "따뜻한" if temp < 4000 else "시원한" if temp > 5000 else "중립"
        return {"success": True, "color_temp": temp, "message": f"거실등 색온도를 {temp}K ({warmth})로 설정했습니다."}

    # === 로봇청소기 함수들 ===

    def vacuum_start(self) -> dict:
        """로봇청소기 청소 시작"""
        self.state.vacuum.power = True
        self.state.vacuum.status = VacuumStatus.CLEANING
        self._notify_change()
        return {"success": True, "status": "cleaning", "message": "청소를 시작합니다."}

    def vacuum_pause(self) -> dict:
        """로봇청소기 일시정지"""
        if self.state.vacuum.status == VacuumStatus.CLEANING:
            self.state.vacuum.status = VacuumStatus.PAUSED
            self._notify_change()
            return {"success": True, "status": "paused", "message": "청소를 일시정지했습니다."}
        return {"success": False, "message": "청소 중이 아닙니다."}

    def vacuum_stop(self) -> dict:
        """로봇청소기 청소 중지"""
        self.state.vacuum.status = VacuumStatus.IDLE
        self.state.vacuum.current_zone = None
        self._notify_change()
        return {"success": True, "status": "idle", "message": "청소를 중지했습니다."}

    def vacuum_clean_zone(self, zone: str) -> dict:
        """로봇청소기 특정 구역 청소"""
        zone_names = {
            "living_room": "거실",
            "bedroom": "침실",
            "kitchen": "주방",
            "bathroom": "화장실"
        }
        zone_lower = zone.lower()
        if zone_lower in zone_names:
            self.state.vacuum.power = True
            self.state.vacuum.status = VacuumStatus.CLEANING
            self.state.vacuum.current_zone = zone_lower
            self._notify_change()
            return {"success": True, "zone": zone_lower, "message": f"{zone_names[zone_lower]} 청소를 시작합니다."}
        return {"success": False, "message": "잘못된 구역입니다. living_room, bedroom, kitchen, bathroom 중 선택하세요."}

    def vacuum_return_dock(self) -> dict:
        """로봇청소기 충전 독 복귀"""
        self.state.vacuum.status = VacuumStatus.RETURNING
        self.state.vacuum.current_zone = None
        self._notify_change()
        return {"success": True, "status": "returning", "message": "충전 독으로 복귀합니다."}

    # === 오디오 함수들 ===

    def audio_power_on(self) -> dict:
        """오디오 켜기"""
        self.state.audio.power = True
        self._notify_change()
        return {"success": True, "message": "오디오를 켰습니다."}

    def audio_power_off(self) -> dict:
        """오디오 끄기"""
        self.state.audio.power = False
        self.state.audio.playback = PlaybackStatus.STOPPED
        self._notify_change()
        return {"success": True, "message": "오디오를 껐습니다."}

    def audio_set_volume(self, volume: int) -> dict:
        """오디오 볼륨 설정 (0-100)"""
        volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, volume))
        self.state.audio.volume = volume
        if not self.state.audio.power:
            self.state.audio.power = True
        self._notify_change()
        return {"success": True, "volume": volume, "message": f"오디오 볼륨을 {volume}으로 설정했습니다."}

    def audio_adjust_volume(self, delta: int) -> dict:
        """오디오 볼륨 증감"""
        new_volume = self.state.audio.volume + delta
        return self.audio_set_volume(new_volume)

    def audio_play(self) -> dict:
        """오디오 재생"""
        self.state.audio.playback = PlaybackStatus.PLAYING
        if not self.state.audio.power:
            self.state.audio.power = True
        self._notify_change()
        return {"success": True, "playback": "playing", "message": "음악을 재생합니다."}

    def audio_pause(self) -> dict:
        """오디오 일시정지"""
        self.state.audio.playback = PlaybackStatus.PAUSED
        self._notify_change()
        return {"success": True, "playback": "paused", "message": "음악을 일시정지했습니다."}

    def audio_stop(self) -> dict:
        """오디오 정지"""
        self.state.audio.playback = PlaybackStatus.STOPPED
        self._notify_change()
        return {"success": True, "playback": "stopped", "message": "음악을 정지했습니다."}

    def audio_play_playlist(self, playlist: str) -> dict:
        """오디오 플레이리스트 재생"""
        self.state.audio.current_playlist = playlist
        self.state.audio.playback = PlaybackStatus.PLAYING
        if not self.state.audio.power:
            self.state.audio.power = True
        self._notify_change()
        return {"success": True, "playlist": playlist, "message": f"{playlist} 플레이리스트를 재생합니다."}

    # === 전동커튼 함수들 ===

    def curtain_open(self) -> dict:
        """전동커튼 열기"""
        self.state.curtain.position = 100
        self.state.curtain.status = CurtainStatus.STOPPED
        self._notify_change()
        return {"success": True, "position": 100, "message": "커튼을 열었습니다."}

    def curtain_close(self) -> dict:
        """전동커튼 닫기"""
        self.state.curtain.position = 0
        self.state.curtain.status = CurtainStatus.STOPPED
        self._notify_change()
        return {"success": True, "position": 0, "message": "커튼을 닫았습니다."}

    def curtain_stop(self) -> dict:
        """전동커튼 멈춤"""
        self.state.curtain.status = CurtainStatus.STOPPED
        self._notify_change()
        return {"success": True, "message": "커튼을 멈췄습니다."}

    def curtain_set_position(self, position: int) -> dict:
        """전동커튼 위치 설정 (0-100%, 0=닫힘, 100=열림)"""
        position = max(self.MIN_POSITION, min(self.MAX_POSITION, position))
        self.state.curtain.position = position
        self.state.curtain.status = CurtainStatus.STOPPED
        self._notify_change()
        return {"success": True, "position": position, "message": f"커튼을 {position}% 위치로 설정했습니다."}

    # === 환풍기 함수들 ===

    def ventilation_power_on(self) -> dict:
        """환풍기 켜기"""
        self.state.ventilation.power = True
        self._notify_change()
        return {"success": True, "message": "환풍기를 켰습니다."}

    def ventilation_power_off(self) -> dict:
        """환풍기 끄기"""
        self.state.ventilation.power = False
        self._notify_change()
        return {"success": True, "message": "환풍기를 껐습니다."}

    def ventilation_set_speed(self, speed: str) -> dict:
        """환풍기 속도 설정"""
        try:
            self.state.ventilation.speed = FanSpeed(speed.lower())
            if not self.state.ventilation.power:
                self.state.ventilation.power = True
            self._notify_change()
            return {"success": True, "speed": speed, "message": f"환풍기 속도를 {speed}로 설정했습니다."}
        except ValueError:
            return {"success": False, "message": "잘못된 속도입니다."}

    # === 함수 실행기 ===

    def execute_function(self, function_name: str, parameters: dict = None) -> dict:
        """함수 이름과 파라미터로 함수 실행"""
        parameters = parameters or {}

        function_map = {
            # 에어컨
            "ac_power_on": self.ac_power_on,
            "ac_power_off": self.ac_power_off,
            "ac_set_temperature": lambda: self.ac_set_temperature(int(parameters.get("temperature", 24))),
            "ac_adjust_temperature": lambda: self.ac_adjust_temperature(int(parameters.get("delta", 0))),
            "ac_set_mode": lambda: self.ac_set_mode(parameters.get("mode", "cooling")),
            "ac_set_fan_speed": lambda: self.ac_set_fan_speed(parameters.get("speed", "auto")),
            # TV
            "tv_power_on": self.tv_power_on,
            "tv_power_off": self.tv_power_off,
            "tv_set_channel": lambda: self.tv_set_channel(int(parameters.get("channel", 1))),
            "tv_set_volume": lambda: self.tv_set_volume(int(parameters.get("volume", 30))),
            "tv_adjust_volume": lambda: self.tv_adjust_volume(int(parameters.get("delta", 0))),
            "tv_launch_app": lambda: self.tv_launch_app(parameters.get("app_name", "")),
            # 거실등
            "light_power_on": self.light_power_on,
            "light_power_off": self.light_power_off,
            "light_set_brightness": lambda: self.light_set_brightness(int(parameters.get("brightness", 100))),
            "light_adjust_brightness": lambda: self.light_adjust_brightness(int(parameters.get("delta", 0))),
            "light_set_color_temp": lambda: self.light_set_color_temp(int(parameters.get("temp", 4000))),
            # 로봇청소기
            "vacuum_start": self.vacuum_start,
            "vacuum_pause": self.vacuum_pause,
            "vacuum_stop": self.vacuum_stop,
            "vacuum_clean_zone": lambda: self.vacuum_clean_zone(parameters.get("zone", "living_room")),
            "vacuum_return_dock": self.vacuum_return_dock,
            # 오디오
            "audio_power_on": self.audio_power_on,
            "audio_power_off": self.audio_power_off,
            "audio_set_volume": lambda: self.audio_set_volume(int(parameters.get("volume", 30))),
            "audio_adjust_volume": lambda: self.audio_adjust_volume(int(parameters.get("delta", 0))),
            "audio_play": self.audio_play,
            "audio_pause": self.audio_pause,
            "audio_stop": self.audio_stop,
            "audio_play_playlist": lambda: self.audio_play_playlist(parameters.get("playlist", "")),
            # 전동커튼
            "curtain_open": self.curtain_open,
            "curtain_close": self.curtain_close,
            "curtain_stop": self.curtain_stop,
            "curtain_set_position": lambda: self.curtain_set_position(int(parameters.get("position", 100))),
            # 환풍기
            "ventilation_power_on": self.ventilation_power_on,
            "ventilation_power_off": self.ventilation_power_off,
            "ventilation_set_speed": lambda: self.ventilation_set_speed(parameters.get("speed", "auto")),
        }

        if function_name in function_map:
            return function_map[function_name]()
        else:
            return {"success": False, "message": f"알 수 없는 함수: {function_name}"}


# === FunctionGemma용 함수 스키마 정의 ===

HOME_FUNCTION_SCHEMAS = [
    # === 에어컨 (6개) ===
    {
        "type": "function",
        "function": {
            "name": "ac_power_on",
            "description": "에어컨 전원을 켭니다. (켜줘/에어컨 켜)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ac_power_off",
            "description": "에어컨 전원을 끕니다. (꺼줘/에어컨 끄기)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ac_set_temperature",
            "description": "에어컨 목표 온도를 설정합니다 (16-30도).",
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {"type": "integer", "description": "목표 온도 (섭씨 16-30)"}
                },
                "required": ["temperature"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ac_adjust_temperature",
            "description": "에어컨 온도를 상대값으로 조절합니다. 양수는 올림, 음수는 내림.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta": {"type": "integer", "description": "온도 변화값 (양수: 올림, 음수: 내림)"}
                },
                "required": ["delta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ac_set_mode",
            "description": "에어컨 모드를 설정합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["cooling", "heating", "auto", "ventilation"], "description": "에어컨 모드"}
                },
                "required": ["mode"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ac_set_fan_speed",
            "description": "에어컨 팬 속도를 설정합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {"type": "string", "enum": ["low", "medium", "high", "auto"], "description": "팬 속도"}
                },
                "required": ["speed"]
            }
        }
    },
    # === TV (6개) ===
    {
        "type": "function",
        "function": {
            "name": "tv_power_on",
            "description": "TV 전원을 켭니다. (TV 켜줘)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tv_power_off",
            "description": "TV 전원을 끕니다. (TV 꺼줘)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tv_set_channel",
            "description": "TV 채널을 설정합니다 (1-100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "integer", "description": "채널 번호 (1-100)"}
                },
                "required": ["channel"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tv_set_volume",
            "description": "TV 볼륨을 설정합니다 (0-100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "volume": {"type": "integer", "description": "볼륨 (0-100)"}
                },
                "required": ["volume"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tv_adjust_volume",
            "description": "TV 볼륨을 상대값으로 조절합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta": {"type": "integer", "description": "볼륨 변화값"}
                },
                "required": ["delta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tv_launch_app",
            "description": "TV 앱을 실행합니다 (Netflix, YouTube 등).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "enum": [
                            "Netflix",
                            "YouTube",
                            "Disney+",
                            "Wavve",
                            "Tving",
                            "TVING",
                            "Watcha",
                            "Coupang Play",
                            "Amazon Prime",
                            "Apple TV",
                            "Laftel"
                        ],
                        "description": "앱 이름 (Netflix, YouTube 등)"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    # === 거실등 (5개) ===
    {
        "type": "function",
        "function": {
            "name": "light_power_on",
            "description": "거실등 전원을 켭니다. (불 켜줘/조명 켜)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "light_power_off",
            "description": "거실등 전원을 끕니다. (불 꺼줘/조명 끄기)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "light_set_brightness",
            "description": "거실등 밝기를 설정합니다 (0-100%).",
            "parameters": {
                "type": "object",
                "properties": {
                    "brightness": {"type": "integer", "description": "밝기 (0-100%)"}
                },
                "required": ["brightness"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "light_adjust_brightness",
            "description": "거실등 밝기를 상대값으로 조절합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta": {"type": "integer", "description": "밝기 변화값"}
                },
                "required": ["delta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "light_set_color_temp",
            "description": "거실등 색온도(켈빈)를 설정합니다 (2700K 따뜻한 ~ 6500K 시원한).",
            "parameters": {
                "type": "object",
                "properties": {
                    "temp": {"type": "integer", "description": "색온도/켈빈 (2700-6500K)"}
                },
                "required": ["temp"]
            }
        }
    },
    # === 로봇청소기 (5개) ===
    {
        "type": "function",
        "function": {
            "name": "vacuum_start",
            "description": "로봇청소기 청소를 시작합니다. (돌려줘/청소 시작)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vacuum_pause",
            "description": "로봇청소기 청소를 일시정지합니다.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vacuum_stop",
            "description": "로봇청소기 청소를 중지합니다. (끄기/정지/멈춤)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vacuum_clean_zone",
            "description": "로봇청소기가 특정 구역을 청소합니다. (거실/침실/주방/화장실)",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {"type": "string", "enum": ["living_room", "bedroom", "kitchen", "bathroom"], "description": "청소 구역"}
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vacuum_return_dock",
            "description": "로봇청소기를 충전 독으로 복귀시킵니다.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    # === 오디오 (8개) ===
    {
        "type": "function",
        "function": {
            "name": "audio_power_on",
            "description": "오디오 시스템 전원을 켭니다. (오디오 켜줘)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audio_power_off",
            "description": "오디오 시스템 전원을 끕니다. (오디오 꺼줘)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audio_set_volume",
            "description": "오디오 볼륨을 설정합니다 (0-100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "volume": {"type": "integer", "description": "볼륨 (0-100)"}
                },
                "required": ["volume"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audio_adjust_volume",
            "description": "오디오 볼륨을 상대값으로 조절합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta": {"type": "integer", "description": "볼륨 변화값"}
                },
                "required": ["delta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audio_play",
            "description": "오디오를 재생합니다.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audio_pause",
            "description": "오디오를 일시정지합니다.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audio_stop",
            "description": "오디오를 정지합니다.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "audio_play_playlist",
            "description": "특정 플레이리스트를 재생합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist": {"type": "string", "description": "플레이리스트 이름"}
                },
                "required": ["playlist"]
            }
        }
    },
    # === 전동커튼 (4개) ===
    {
        "type": "function",
        "function": {
            "name": "curtain_open",
            "description": "전동커튼을 엽니다. (커튼 열어줘)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "curtain_close",
            "description": "전동커튼을 닫습니다. (커튼 닫아줘)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "curtain_stop",
            "description": "전동커튼 작동을 멈춥니다. (멈춰/정지)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "curtain_set_position",
            "description": "전동커튼 위치를 설정합니다 (0=닫힘, 100=열림, 퍼센트/프로).",
            "parameters": {
                "type": "object",
                "properties": {
                    "position": {"type": "integer", "description": "위치 (0-100%, 퍼센트/프로)"}
                },
                "required": ["position"]
            }
        }
    },
    # === 환풍기 (3개) ===
    {
        "type": "function",
        "function": {
            "name": "ventilation_power_on",
            "description": "환풍기 전원을 켭니다. (켜줘/환기)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ventilation_power_off",
            "description": "환풍기 전원을 끕니다. (꺼줘/끄다/정지)",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ventilation_set_speed",
            "description": "환풍기 속도를 설정합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {"type": "string", "enum": ["low", "medium", "high", "auto"], "description": "환풍기 속도"}
                },
                "required": ["speed"]
            }
        }
    }
]
# Total: 37 functions
