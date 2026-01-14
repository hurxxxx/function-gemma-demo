# FunctionGemma Home IoT Voice Control Demo

FunctionGemma를 활용한 스마트홈 IoT 음성/텍스트 제어 데모 애플리케이션입니다.

## 주요 기능
- **음성 인식**: 한국어 음성 명령을 텍스트로 변환 (Whisper)
- **자연어 → 함수 호출**: FunctionGemma가 명령을 함수 호출로 변환
- **멀티 기기 제어**: 7개 기기 동시 제어 지원
- **실시간 상태 동기화**: WebSocket으로 상태 즉시 반영

## 지원 기기
- 에어컨, TV, 거실등, 로봇청소기, 오디오, 전동커튼, 환풍기

## 데모 명령 모음
- `docs/demo-commands.md`

## 테스트 리포트
- `docs/functiongemma-test-report.md`

## 빠른 실행
```bash
./run_all.sh
```

- 백엔드: http://localhost:18080
- 프론트엔드: http://localhost:15173

## 수동 실행

### 백엔드
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev
```

## LoRA 어댑터
- `training/output_lora/adapter_model.safetensors`
- `training/output_lora/adapter_config.json`

## 프로젝트 구조 (요약)
```
function-gemma-demo/
├── backend/
│   ├── main.py
│   ├── home_controller.py
│   ├── function_gemma.py
│   └── speech_to_text.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── components/devices/
├── training/
│   ├── finetune_lora.py
│   ├── run_finetune.sh
│   └── output_lora/
└── docs/
```

## API 엔드포인트
| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/state` | GET | 현재 홈 상태 조회 |
| `/command/text` | POST | 텍스트 명령 처리 |
| `/command/voice` | POST | 음성 파일 처리 |
| `/ws` | WebSocket | 실시간 상태 업데이트 |

## 문서
- `docs/functiongemma-usage.md`
- `docs/functiongemma-finetune.md`
- `docs/fine-tuning.md`

## 라이선스
MIT License
