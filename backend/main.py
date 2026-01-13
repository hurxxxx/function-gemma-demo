"""
FunctionGemma 홈 IoT 음성 제어 API
7개 기기: 에어컨, TV, 거실등, 로봇청소기, 오디오, 전동커튼, 환풍기
"""
import asyncio
import json
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from home_controller import HomeController, HomeState
from function_gemma import get_model
from speech_to_text import get_stt


app = FastAPI(
    title="FunctionGemma Home IoT Controller",
    description="홈 IoT 음성 제어 데모 API",
    version="2.0.0"
)

# CORS 설정 (개발용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 연결 관리
connected_clients: Set[WebSocket] = set()


async def broadcast_state(state: dict):
    """모든 연결된 클라이언트에게 상태 전송"""
    if connected_clients:
        message = json.dumps({
            "type": "state_update",
            "state": state
        })
        disconnected = set()
        for client in connected_clients:
            try:
                await client.send_text(message)
            except:
                disconnected.add(client)
        connected_clients.difference_update(disconnected)


def on_state_change(state: dict):
    """홈 상태 변경 콜백"""
    asyncio.create_task(broadcast_state(state))


# 홈 컨트롤러 인스턴스
home_controller = HomeController(on_state_change=on_state_change)


class TextCommand(BaseModel):
    """텍스트 명령"""
    text: str


class CommandResponse(BaseModel):
    """명령 응답"""
    success: bool
    input_text: str
    function_call: dict | None
    function_calls: list[dict] | None = None
    result: dict | None
    results: list[dict] | None = None
    raw_output: str | None


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    print("Loading models...")
    # 백그라운드에서 모델 로드 (시작 시간 단축을 위해)
    # 실제 요청 시 로드됨


@app.get("/")
async def root():
    """헬스 체크"""
    return {"status": "ok", "message": "FunctionGemma Home IoT Controller API"}


@app.get("/state")
async def get_state():
    """현재 홈 상태 조회"""
    return home_controller.state.to_dict()


@app.post("/command/text", response_model=CommandResponse)
async def process_text_command(command: TextCommand):
    """
    텍스트 명령 처리

    자연어 텍스트를 받아서 FunctionGemma로 함수 호출 생성,
    홈 기기 상태 변경 후 결과 반환
    """
    model = get_model()

    # 함수 호출 생성
    generation_result = model.generate_function_call(
        command.text,
        context=home_controller.state.to_dict()
    )

    if not generation_result["success"]:
        return CommandResponse(
            success=False,
            input_text=command.text,
            function_call=None,
            result={"message": "함수 호출을 생성하지 못했습니다."},
            raw_output=generation_result["raw_output"]
        )

    function_calls = generation_result.get("function_calls") or []
    if not function_calls and generation_result.get("function_call"):
        function_calls = [generation_result["function_call"]]

    # 함수 실행 (멀티턴: 여러 함수 순차 실행)
    results = []
    for function_call in function_calls:
        results.append(
            home_controller.execute_function(
                function_call["function_name"],
                function_call["parameters"]
            )
        )

    function_call = function_calls[0] if function_calls else None
    result = results[0] if results else None

    return CommandResponse(
        success=True,
        input_text=command.text,
        function_call=function_call,
        function_calls=function_calls,
        result=result,
        results=results,
        raw_output=generation_result["raw_output"]
    )


@app.post("/command/voice")
async def process_voice_command(audio: UploadFile = File(...)):
    """
    음성 명령 처리

    음성 파일을 받아서:
    1. Whisper로 텍스트 변환
    2. FunctionGemma로 함수 호출 생성
    3. 홈 기기 상태 변경
    """
    # 음성 -> 텍스트
    stt = get_stt("base")
    audio_bytes = await audio.read()
    transcription = stt.transcribe_bytes(audio_bytes)

    if not transcription["success"]:
        raise HTTPException(
            status_code=400,
            detail=f"음성 인식 실패: {transcription.get('error', 'Unknown error')}"
        )

    recognized_text = transcription["text"]

    if not recognized_text:
        return {
            "success": False,
            "transcription": "",
            "message": "음성을 인식하지 못했습니다."
        }

    # 텍스트 명령 처리
    model = get_model()
    generation_result = model.generate_function_call(
        recognized_text,
        context=home_controller.state.to_dict()
    )

    if not generation_result["success"]:
        return {
            "success": False,
            "transcription": recognized_text,
            "function_call": None,
            "result": {"message": "함수 호출을 생성하지 못했습니다."},
            "raw_output": generation_result["raw_output"]
        }

    function_calls = generation_result.get("function_calls") or []
    if not function_calls and generation_result.get("function_call"):
        function_calls = [generation_result["function_call"]]

    # 함수 실행 (멀티턴: 여러 함수 순차 실행)
    results = []
    for function_call in function_calls:
        results.append(
            home_controller.execute_function(
                function_call["function_name"],
                function_call["parameters"]
            )
        )

    function_call = function_calls[0] if function_calls else None
    result = results[0] if results else None

    return {
        "success": True,
        "transcription": recognized_text,
        "detected_language": transcription.get("language", "unknown"),
        "function_call": function_call,
        "function_calls": function_calls,
        "result": result,
        "results": results,
        "raw_output": generation_result["raw_output"]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결 - 실시간 상태 업데이트"""
    await websocket.accept()
    connected_clients.add(websocket)

    # 초기 상태 전송
    await websocket.send_text(json.dumps({
        "type": "state_update",
        "state": home_controller.state.to_dict()
    }))

    try:
        while True:
            # 클라이언트로부터 메시지 수신 (keepalive)
            data = await websocket.receive_text()

            # ping/pong 처리
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connected_clients.discard(websocket)


# === 에어컨 직접 제어 API ===

@app.post("/device/ac/power/{action}")
async def ac_power_control(action: str):
    """에어컨 전원 제어"""
    if action == "on":
        return home_controller.ac_power_on()
    elif action == "off":
        return home_controller.ac_power_off()
    else:
        raise HTTPException(status_code=400, detail="action must be 'on' or 'off'")


@app.post("/device/ac/temperature/{temperature}")
async def ac_set_temp(temperature: int):
    """에어컨 온도 설정"""
    return home_controller.ac_set_temperature(temperature)


@app.post("/device/ac/mode/{mode}")
async def ac_set_mode(mode: str):
    """에어컨 모드 설정"""
    return home_controller.ac_set_mode(mode)


@app.post("/device/ac/fan/{speed}")
async def ac_set_fan(speed: str):
    """에어컨 팬 속도 설정"""
    return home_controller.ac_set_fan_speed(speed)


# === TV 직접 제어 API ===

@app.post("/device/tv/power/{action}")
async def tv_power_control(action: str):
    """TV 전원 제어"""
    if action == "on":
        return home_controller.tv_power_on()
    elif action == "off":
        return home_controller.tv_power_off()
    else:
        raise HTTPException(status_code=400, detail="action must be 'on' or 'off'")


@app.post("/device/tv/channel/{channel}")
async def tv_set_channel(channel: int):
    """TV 채널 설정"""
    return home_controller.tv_set_channel(channel)


@app.post("/device/tv/volume/{volume}")
async def tv_set_volume(volume: int):
    """TV 볼륨 설정"""
    return home_controller.tv_set_volume(volume)


@app.post("/device/tv/app/{app_name}")
async def tv_launch_app(app_name: str):
    """TV 앱 실행"""
    return home_controller.tv_launch_app(app_name)


# === 거실등 직접 제어 API ===

@app.post("/device/light/power/{action}")
async def light_power_control(action: str):
    """거실등 전원 제어"""
    if action == "on":
        return home_controller.light_power_on()
    elif action == "off":
        return home_controller.light_power_off()
    else:
        raise HTTPException(status_code=400, detail="action must be 'on' or 'off'")


@app.post("/device/light/brightness/{brightness}")
async def light_set_brightness(brightness: int):
    """거실등 밝기 설정"""
    return home_controller.light_set_brightness(brightness)


@app.post("/device/light/color_temp/{temp}")
async def light_set_color_temp(temp: int):
    """거실등 색온도 설정"""
    return home_controller.light_set_color_temp(temp)


# === 로봇청소기 직접 제어 API ===

@app.post("/device/vacuum/command/{command}")
async def vacuum_command(command: str):
    """로봇청소기 명령"""
    commands = {
        "start": home_controller.vacuum_start,
        "pause": home_controller.vacuum_pause,
        "stop": home_controller.vacuum_stop,
        "dock": home_controller.vacuum_return_dock,
    }
    if command in commands:
        return commands[command]()
    else:
        raise HTTPException(status_code=400, detail="command must be 'start', 'pause', 'stop', or 'dock'")


@app.post("/device/vacuum/zone/{zone}")
async def vacuum_clean_zone(zone: str):
    """로봇청소기 구역 청소"""
    return home_controller.vacuum_clean_zone(zone)


# === 오디오 직접 제어 API ===

@app.post("/device/audio/power/{action}")
async def audio_power_control(action: str):
    """오디오 전원 제어"""
    if action == "on":
        return home_controller.audio_power_on()
    elif action == "off":
        return home_controller.audio_power_off()
    else:
        raise HTTPException(status_code=400, detail="action must be 'on' or 'off'")


@app.post("/device/audio/volume/{volume}")
async def audio_set_volume(volume: int):
    """오디오 볼륨 설정"""
    return home_controller.audio_set_volume(volume)


@app.post("/device/audio/playback/{command}")
async def audio_playback(command: str):
    """오디오 재생 제어"""
    commands = {
        "play": home_controller.audio_play,
        "pause": home_controller.audio_pause,
        "stop": home_controller.audio_stop,
    }
    if command in commands:
        return commands[command]()
    else:
        raise HTTPException(status_code=400, detail="command must be 'play', 'pause', or 'stop'")


@app.post("/device/audio/playlist/{playlist}")
async def audio_play_playlist(playlist: str):
    """오디오 플레이리스트 재생"""
    return home_controller.audio_play_playlist(playlist)


# === 전동커튼 직접 제어 API ===

@app.post("/device/curtain/command/{command}")
async def curtain_command(command: str):
    """전동커튼 명령"""
    commands = {
        "open": home_controller.curtain_open,
        "close": home_controller.curtain_close,
        "stop": home_controller.curtain_stop,
    }
    if command in commands:
        return commands[command]()
    else:
        raise HTTPException(status_code=400, detail="command must be 'open', 'close', or 'stop'")


@app.post("/device/curtain/position/{position}")
async def curtain_set_position(position: int):
    """전동커튼 위치 설정"""
    return home_controller.curtain_set_position(position)


# === 환풍기 직접 제어 API ===

@app.post("/device/ventilation/power/{action}")
async def ventilation_power_control(action: str):
    """환풍기 전원 제어"""
    if action == "on":
        return home_controller.ventilation_power_on()
    elif action == "off":
        return home_controller.ventilation_power_off()
    else:
        raise HTTPException(status_code=400, detail="action must be 'on' or 'off'")


@app.post("/device/ventilation/speed/{speed}")
async def ventilation_set_speed(speed: str):
    """환풍기 속도 설정"""
    return home_controller.ventilation_set_speed(speed)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18080)
