# 서버 업데이트 방법

코드를 수정하고 GitHub에 push한 후, 서버에서 다음 명령어를 실행하세요.

## 서버에서 실행

```bash
# SSH로 서버 접속
ssh koast-user@10.1.10.128

# 프로젝트 디렉토리로 이동
cd ~/edge-system-checker-web

# 최신 코드 가져오기
git pull origin main

# 서비스 재시작
cd backend
source venv/bin/activate

# 현재 실행 중인 서버가 있으면 Ctrl+C로 중지하고
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 또는 systemd 서비스로 실행 중이라면
# sudo systemctl restart edge-checker-web
```

## 변경 사항

### 이번 업데이트 내용:

1. **datetime 직렬화 오류 수정**
   - DB 저장 시 datetime 객체를 자동으로 ISO 문자열로 변환
   - 더 이상 JSON serialization 오류가 발생하지 않음

2. **프론트엔드 상세 정보 표시 개선**
   - 카메라: 원본/블러/로그 상태를 각각 표시
   - UPS: 서비스 상태, UPS 상태, 배터리 잔량 표시
   - NAS: SSH 연결, 디스크 정보 표시
   - 시스템: 통계(✓✗⚠◌) 및 실패 항목 목록 표시

3. **실시간 진행률 표시 개선**
   - WebSocket 메시지를 콘솔에 로깅 (디버그용)
   - 진행 중일 때 스피너 아이콘 표시
   - 더 명확한 상태 메시지 표시

## 빠른 업데이트 스크립트

```bash
ssh koast-user@10.1.10.128 << 'EOF'
cd ~/edge-system-checker-web
git pull origin main
sudo systemctl restart edge-checker-web 2>/dev/null || echo "Manual restart needed"
sudo systemctl status edge-checker-web --no-pager
EOF
```

## 수동 재시작이 필요한 경우

```bash
ssh koast-user@10.1.10.128
cd ~/edge-system-checker-web/backend
source venv/bin/activate

# 기존 프로세스 찾기
ps aux | grep uvicorn

# 프로세스 종료 (PID를 실제 값으로 변경)
kill <PID>

# 재시작
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &

# 로그 확인
tail -f app.log
```

## 확인

웹 브라우저에서 `http://10.1.10.128:8000` 새로고침 후 점검 실행

