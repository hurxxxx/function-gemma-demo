# FunctionGemma Home IoT Voice Control Demo

Korean: [README.ko.md](README.ko.md)

FunctionGemma-based smart home voice/text control demo.

## Features
- Korean speech recognition via Whisper
- Natural language -> function calls with FunctionGemma
- Multi-device control (7 devices)
- Real-time state sync over WebSocket

## Supported Devices
- Air conditioner, TV, living room light, robot vacuum, audio, curtains, ventilation fan

## Demo Commands
- docs/demo-commands.md

## Test Report
- docs/functiongemma-test-report.md

## Quick Start
```bash
./run_all.sh
```

- Backend: http://localhost:18080
- Frontend: http://localhost:15173

## Manual Run

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## LoRA Adapter
- training/output_lora/adapter_model.safetensors
- training/output_lora/adapter_config.json

## Project Layout (Summary)
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

## Documentation
- docs/functiongemma-usage.md
- docs/functiongemma-finetune.md
- docs/fine-tuning.md
- docs/functiongemma-test-report.md
- docs/demo-commands.md

## License
MIT License
