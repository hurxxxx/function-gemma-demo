#!/bin/bash
# Frontend 실행 스크립트

cd "$(dirname "$0")/frontend"

# 의존성 설치
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# 개발 서버 실행
echo "Starting frontend on http://localhost:5173"
npm run dev
