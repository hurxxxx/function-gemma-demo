# FunctionGemma Car A/C Voice Control Demo

FunctionGemma를 활용한 차량용 에어컨 음성 제어 데모 애플리케이션입니다.

## 주요 기능

- **음성 인식**: 한국어 음성 명령을 텍스트로 변환 (Whisper)
- **자연어 → 함수 호출**: FunctionGemma가 자연어를 에어컨 제어 함수로 변환
- **실시간 상태 동기화**: WebSocket으로 에어컨 상태 실시간 반영

## 지원하는 음성 명령 예시

| 명령 | 동작 |
|-----|------|
| "온도 올려줘" | 온도 +2도 |
| "온도 내려줘" | 온도 -2도 |
| "오늘 날씨가 덥네" | 자동으로 온도 낮춤 |
| "여름철 적정 온도로 맞춰줘" | 25도로 설정 |
| "바람 세게 해줘" | 팬 속도 high |
| "에어컨 꺼줘" | 전원 off |

## 시스템 요구사항

### 백엔드
- Python 3.10+
- 최소 4GB RAM (8GB 권장)
- 라즈베리파이4 지원

### 프론트엔드
- Node.js 18+
- 최신 웹 브라우저 (마이크 접근 필요)

## 설치 및 실행

### 1. 백엔드 설치 및 실행

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (첫 실행 시 모델 다운로드로 시간 소요)
pip install -r requirements.txt

# 서버 실행
python main.py
```

백엔드 서버: http://localhost:8000

### 2. 프론트엔드 설치 및 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드: http://localhost:5173

## 프로젝트 구조

```
function-gemma-demo/
├── backend/
│   ├── main.py              # FastAPI 앱 + WebSocket
│   ├── ac_controller.py     # 에어컨 상태 관리
│   ├── function_gemma.py    # FunctionGemma 모델 래퍼
│   ├── speech_to_text.py    # Whisper STT
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ACDisplay.tsx     # 에어컨 UI
│   │   │   ├── VoiceRecorder.tsx # 음성 녹음
│   │   │   └── CommandLog.tsx    # 명령 로그
│   │   └── hooks/
│   │       └── useWebSocket.ts   # WebSocket 훅
│   └── package.json
└── README.md
```

## API 엔드포인트

| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/state` | GET | 현재 에어컨 상태 조회 |
| `/command/text` | POST | 텍스트 명령 처리 |
| `/command/voice` | POST | 음성 파일 처리 |
| `/ws` | WebSocket | 실시간 상태 업데이트 |

## 기술 스택

- **Backend**: FastAPI, WebSocket, Transformers
- **AI Models**: FunctionGemma (270M), Whisper (base)
- **Frontend**: React, TypeScript, Vite

## 라이선스

MIT License
