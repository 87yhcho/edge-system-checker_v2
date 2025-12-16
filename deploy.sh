#!/bin/bash
# 원격 서버 배포 스크립트

# 설정
SERVER_USER="koast-user"
SERVER_HOST="10.1.10.128"
SERVER_PATH="~/edge-system-checker-web"
LOCAL_PATH="."

echo "=========================================="
echo "Edge System Checker Web 배포 스크립트"
echo "=========================================="
echo ""

# 1. Git 상태 확인
echo "1. Git 상태 확인 중..."
if [ -d ".git" ]; then
    echo "✓ Git 저장소 확인됨"
    git status
else
    echo "⚠ Git 저장소가 초기화되지 않았습니다."
    read -p "Git 저장소를 초기화하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git init
        git add .
        git commit -m "Initial commit: Edge System Checker Web"
    fi
fi

# 2. 원격 저장소 확인
echo ""
echo "2. 원격 저장소 확인 중..."
if git remote | grep -q "origin"; then
    echo "✓ 원격 저장소 확인됨: $(git remote get-url origin)"
    read -p "원격 저장소에 푸시하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin main || git push origin master
    fi
else
    echo "⚠ 원격 저장소가 설정되지 않았습니다."
    echo "다음 명령어로 원격 저장소를 추가하세요:"
    echo "  git remote add origin <repository-url>"
fi

# 3. 서버에 파일 전송
echo ""
echo "3. 서버에 파일 전송 중..."
echo "서버: ${SERVER_USER}@${SERVER_HOST}"
echo "경로: ${SERVER_PATH}"

read -p "계속하시겠습니까? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "배포가 취소되었습니다."
    exit 1
fi

# rsync를 사용하여 파일 전송 (권장)
if command -v rsync &> /dev/null; then
    echo "rsync를 사용하여 파일 전송 중..."
    rsync -avz --exclude='.git' \
              --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='venv' \
              --exclude='.env' \
              --exclude='*.db' \
              --exclude='*.log' \
              "${LOCAL_PATH}/" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"
else
    echo "rsync가 설치되지 않았습니다. scp를 사용합니다..."
    scp -r "${LOCAL_PATH}" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}"
fi

echo "✓ 파일 전송 완료"

# 4. 서버에서 설정 실행
echo ""
echo "4. 서버에서 설정 실행 중..."
echo "다음 명령어를 서버에서 실행하세요:"
echo ""
echo "  ssh ${SERVER_USER}@${SERVER_HOST}"
echo "  cd ${SERVER_PATH}/backend"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  cp ../env.example .env"
echo "  nano .env  # 환경 변수 설정"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "또는 systemd 서비스로 등록:"
echo "  sudo systemctl start edge-checker-web"
echo ""
echo "=========================================="
echo "배포 스크립트 완료"
echo "=========================================="

