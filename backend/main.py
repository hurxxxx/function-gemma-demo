"""
FunctionGemma 차량용 에어컨 음성 제어 API
"""
import asyncio
import json
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ac_controller import ACController, ACState
from function_gemma import get_model
from speech_to_text import get_stt


app = FastAPI(
    title="FunctionGemma AC Controller",
    description="차량용 에어컨 음성 제어 데모 API",
    version="1.0.0"
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
    """에어컨 상태 변경 콜백"""
    asyncio.create_task(broadcast_state(state))


# 에어컨 컨트롤러 인스턴스
ac_controller = ACController(on_state_change=on_state_change)


class TextCommand(BaseModel):
    """텍스트 명령"""
    text: str


class CommandResponse(BaseModel):
    """명령 응답"""
    success: bool
    input_text: str
    function_call: dict | None
    result: dict | None
    raw_output: str | None


class EnvironmentUpdate(BaseModel):
    """실내/외기 온도 업데이트"""
    indoor_temperature: int | None = None
    outdoor_temperature: int | None = None


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    print("Loading models...")
    # 백그라운드에서 모델 로드 (시작 시간 단축을 위해)
    # 실제 요청 시 로드됨


@app.get("/")
async def root():
    """헬스 체크"""
    return {"status": "ok", "message": "FunctionGemma AC Controller API"}


@app.get("/state")
async def get_state():
    """현재 에어컨 상태 조회"""
    return ac_controller.state.to_dict()


@app.post("/command/text", response_model=CommandResponse)
async def process_text_command(command: TextCommand):
    """
    텍스트 명령 처리

    자연어 텍스트를 받아서 FunctionGemma로 함수 호출 생성,
    에어컨 상태 변경 후 결과 반환
    """
    model = get_model()

    # 함수 호출 생성
    generation_result = model.generate_function_call(
        command.text,
        context=ac_controller.state.to_dict()
    )

    if not generation_result["success"]:
        return CommandResponse(
            success=False,
            input_text=command.text,
            function_call=None,
            result={"message": "함수 호출을 생성하지 못했습니다."},
            raw_output=generation_result["raw_output"]
        )

    function_call = generation_result["function_call"]

    # 함수 실행
    result = ac_controller.execute_function(
        function_call["function_name"],
        function_call["parameters"]
    )

    return CommandResponse(
        success=True,
        input_text=command.text,
        function_call=function_call,
        result=result,
        raw_output=generation_result["raw_output"]
    )


@app.post("/command/voice")
async def process_voice_command(audio: UploadFile = File(...)):
    """
    음성 명령 처리

    음성 파일을 받아서:
    1. Whisper로 텍스트 변환
    2. FunctionGemma로 함수 호출 생성
    3. 에어컨 상태 변경
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
        context=ac_controller.state.to_dict()
    )

    if not generation_result["success"]:
        return {
            "success": False,
            "transcription": recognized_text,
            "function_call": None,
            "result": {"message": "함수 호출을 생성하지 못했습니다."},
            "raw_output": generation_result["raw_output"]
        }

    function_call = generation_result["function_call"]

    # 함수 실행
    result = ac_controller.execute_function(
        function_call["function_name"],
        function_call["parameters"]
    )

    return {
        "success": True,
        "transcription": recognized_text,
        "detected_language": transcription.get("language", "unknown"),
        "function_call": function_call,
        "result": result,
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
        "state": ac_controller.state.to_dict()
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


# 직접 상태 변경 API (테스트/수동 조작용)
@app.post("/ac/power/{action}")
async def power_control(action: str):
    """전원 제어"""
    if action == "on":
        return ac_controller.power_on()
    elif action == "off":
        return ac_controller.power_off()
    else:
        raise HTTPException(status_code=400, detail="action must be 'on' or 'off'")


@app.post("/ac/temperature/{temperature}")
async def set_temp(temperature: int):
    """온도 설정"""
    return ac_controller.set_temperature(temperature)


@app.post("/ac/fan/{speed}")
async def set_fan(speed: str):
    """팬 속도 설정"""
    return ac_controller.set_fan_speed(speed)


@app.post("/ac/mode/{mode}")
async def set_mode(mode: str):
    """모드 설정"""
    return ac_controller.set_mode(mode)


@app.post("/environment")
async def update_environment(update: EnvironmentUpdate):
    """실내/외기 온도 업데이트"""
    if update.indoor_temperature is None and update.outdoor_temperature is None:
        raise HTTPException(
            status_code=400,
            detail="indoor_temperature 또는 outdoor_temperature 중 하나 이상 필요합니다."
        )

    return ac_controller.update_environment(
        indoor_temperature=update.indoor_temperature,
        outdoor_temperature=update.outdoor_temperature
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
