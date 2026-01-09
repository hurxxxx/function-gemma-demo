#!/bin/bash
# Backend 실행 스크립트

cd "$(dirname "$0")/backend"

# 가상환경 생성 (없으면)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
echo "Installing dependencies..."
pip install -r requirements.txt

# 서버 실행
echo "Starting backend server on http://localhost:8000"
python main.py
