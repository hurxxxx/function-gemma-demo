#!/bin/bash

# ===========================================
# FunctionGemma Demo - 통합 실행 스크립트
# 백엔드(8000)와 프론트엔드(5173)를 함께 실행
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_PORT=18080
FRONTEND_PORT=15173
BACKEND_PID=""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 포트 사용 중인 프로세스 종료
kill_port() {
    local port=$1
    local pids=$(lsof -t -i:$port 2>/dev/null || true)

    if [ -n "$pids" ]; then
        log_warn "포트 $port 사용 중인 프로세스 발견: $pids"
        for pid in $pids; do
            log_info "프로세스 $pid 종료 중..."
            kill -9 $pid 2>/dev/null || true
        done
        sleep 1
        log_success "포트 $port 정리 완료"
    else
        log_info "포트 $port 사용 가능"
    fi
}

# 종료 시 백엔드 프로세스도 함께 종료
cleanup() {
    echo ""
    log_info "종료 중..."

    if [ -n "$BACKEND_PID" ]; then
        log_info "백엔드 프로세스($BACKEND_PID) 종료 중..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    # 포트에 남아있는 프로세스 정리
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT

    log_success "모든 프로세스 종료 완료"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 메인 실행
main() {
    echo ""
    echo "=========================================="
    echo "  FunctionGemma Demo 실행"
    echo "=========================================="
    echo ""

    # 기존 포트 정리
    log_info "기존 프로세스 정리 중..."
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    echo ""

    # 백엔드 시작
    log_info "백엔드 시작 중 (포트 $BACKEND_PORT)..."
    cd "$SCRIPT_DIR/backend"

    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        log_error "백엔드 가상환경(venv)이 없습니다. backend/venv를 먼저 생성해주세요."
        exit 1
    fi

    python main.py &
    BACKEND_PID=$!
    log_success "백엔드 시작됨 (PID: $BACKEND_PID)"

    # 백엔드 준비 대기
    sleep 2
    echo ""

    # 프론트엔드 시작
    log_info "프론트엔드 시작 중 (포트 $FRONTEND_PORT)..."
    cd "$SCRIPT_DIR/frontend"

    if [ ! -d "node_modules" ]; then
        log_info "node_modules가 없습니다. npm install 실행 중..."
        npm install
    fi

    echo ""
    echo "=========================================="
    echo "  서버 실행 완료!"
    echo "  프론트엔드: http://localhost:$FRONTEND_PORT"
    echo "  백엔드 API: http://localhost:$BACKEND_PORT"
    echo "  종료: Ctrl+C"
    echo "=========================================="
    echo ""

    npm run dev
}

main
