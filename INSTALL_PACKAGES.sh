#!/bin/bash
# Edge System Checker UV 기반 설치 스크립트
# 모든 Edge 장비용

echo "=========================================="
echo "Edge System Checker UV 설치"
echo "=========================================="
echo ""

# 1. 시스템 패키지 업데이트
echo "1. 시스템 패키지 업데이트 중..."
sudo apt update

# 2. 필수 도구 설치 (curl, git 등)
echo ""
echo "2. 필수 도구 설치 중..."
sudo apt install -y curl git

# 3. Python 기본 패키지
echo ""
echo "3. Python 기본 패키지 설치 중..."
sudo apt install -y python3 python3-dev python3-pip

# 4. OpenCV 시스템 의존성 (libopencv-dev는 선택사항)
echo ""
echo "4. OpenCV 시스템 의존성 설치 중..."
sudo apt install -y libopencv-dev

# 5. PostgreSQL 클라이언트 라이브러리
echo ""
echo "5. PostgreSQL 클라이언트 라이브러리 설치 중..."
sudo apt install -y libpq-dev

# 6. UV 설치
echo ""
echo "6. UV 설치 중..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # PATH 설정 (.local/bin과 .cargo/bin 모두 추가)
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    # .bashrc에도 추가 (영구적)
    if ! grep -q '.local/bin' ~/.bashrc; then
        echo 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    fi
    
    # 설치 후 다시 확인
    source ~/.bashrc 2>/dev/null || true
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    if command -v uv &> /dev/null; then
        echo "✅ UV 설치 완료"
    else
        echo "⚠️ UV 설치가 완료되었지만 경로를 찾을 수 없습니다."
        echo "   다음 명령을 실행해주세요:"
        echo "   source ~/.bashrc"
        echo "   또는 터미널을 재시작하세요."
    fi
else
    echo "✅ UV가 이미 설치되어 있습니다"
fi

# UV PATH 추가 (즉시 적용)
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

echo ""
echo "=========================================="
echo "✅ 모든 패키지 설치 완료!"
echo "=========================================="
echo ""
echo "설치 확인:"
if command -v uv &> /dev/null; then
    echo "  UV 버전: $(uv --version)"
else
    echo "  UV 버전: (설치됨, 터미널 재시작 필요)"
fi
echo "  Python 버전: $(python3 --version)"

echo ""
echo "=========================================="
echo "다음 단계:"
echo "=========================================="
echo ""
echo "1. 환경 변수 설정:"
echo "   cd edge-system-checker"
echo "   cp env.example .env"
echo "   nano .env  # 실제 값으로 수정"
echo ""
echo "2. 프로그램 실행:"
echo "   ./run_edge_checker.sh"
echo ""
echo "또는 직접 실행:"
echo "   uv run checker.py"
