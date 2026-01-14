# FunctionGemma 홈 IoT 음성 제어 데모

English: [README.md](README.md)

FunctionGemma를 활용한 스마트홈 IoT 음성/텍스트 제어 데모입니다.

## 주요 기능
- Whisper 기반 한국어 음성 인식
- 자연어 -> 함수 호출 변환(FunctionGemma)
- 7개 기기 멀티 제어
- WebSocket 기반 실시간 상태 동기화

## 지원 기기
- 에어컨, TV, 거실등, 로봇청소기, 오디오, 전동커튼, 환풍기

## 데모 명령 모음
- docs/demo-commands.ko.md

## 테스트 리포트
- docs/functiongemma-test-report.ko.md
- docs/functiongemma-test-report-raspberrypi.ko.md

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
- training/output_lora/adapter_model.safetensors
- training/output_lora/adapter_config.json

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

## 문서
- docs/functiongemma-usage.ko.md
- docs/functiongemma-finetune.ko.md
- docs/fine-tuning.ko.md
- docs/functiongemma-test-report.ko.md
- docs/functiongemma-test-report-raspberrypi.ko.md
- docs/demo-commands.ko.md

## 라이선스
MIT License
