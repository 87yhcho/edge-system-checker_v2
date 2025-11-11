#!/bin/bash

# Edge System Checker 실행 스크립트 (UV 기반)
echo "=========================================="
echo "    Edge System Checker 실행"
echo "=========================================="
echo

# UV PATH 추가 (먼저 추가)
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# 현재 디렉토리를 스크립트 위치로 변경
cd "$(dirname "$0")"

# UV가 설치되어 있는지 확인
if ! command -v uv &> /dev/null; then
    echo "⚠️  UV가 설치되어 있지 않습니다."
    echo "   UV 설치 중..."
    
    # UV 설치 스크립트
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # PATH 재설정
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    # 설치 확인
    if ! command -v uv &> /dev/null; then
        echo "❌ UV 설치 실패. 터미널을 재시작한 후 다시 실행해주세요."
        echo "   또는 수동으로 설치:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   source ~/.bashrc"
        echo ""
        echo "   또는 python3으로 직접 실행:"
        echo "   python3 checker.py"
        read -p "Press Enter to close..."
        exit 1
    fi
    echo "✅ UV 설치 완료"
fi

echo "✅ UV 확인 완료"
echo "🚀 Edge System Checker를 시작합니다..."
echo

# UV로 의존성 설치 및 프로그램 실행
# 프로젝트를 설치하지 않고 실행만 함
export UV_NO_PROJECT=1
uv pip install -r requirements.txt && python3 checker.py

echo
echo "=========================================="
echo "           프로그램 실행 완료"
echo "=========================================="
read -p "Press Enter to close..."
