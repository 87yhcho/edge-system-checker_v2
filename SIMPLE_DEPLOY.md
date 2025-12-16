# 간단 배포 가이드 (Git 사용)

가장 간단한 배포 방법: 로컬에서 GitHub에 올리고, 서버에서 Git으로 가져오기

## 1단계: 로컬에서 GitHub에 올리기

### 1.1 GitHub 저장소 생성

1. https://github.com 접속 및 로그인
2. 우측 상단 "+" 버튼 → "New repository"
3. 저장소 이름: `edge-system-checker-web`
4. "Create repository" 클릭

### 1.2 로컬에서 GitHub에 업로드

```powershell
# PowerShell에서 실행
cd E:\cursor\edge-system-checker-web

# Git 초기화
git init

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: Edge System Checker Web"

# 원격 저장소 연결 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/edge-system-checker-web.git

# 업로드
git push -u origin main
```

**참고**: GitHub 인증 시 Personal Access Token이 필요합니다.
- Settings → Developer settings → Personal access tokens → Generate new token
- `repo` 권한 선택
- 생성된 토큰을 비밀번호 대신 사용

## 2단계: 서버에서 다운로드 및 실행

### 2.1 서버 접속

```bash
ssh koast-user@10.1.10.128
```

### 2.2 Git에서 프로젝트 다운로드

```bash
# 홈 디렉토리로 이동
cd ~

# GitHub에서 클론 (YOUR_USERNAME을 실제 사용자명으로 변경)
git clone https://github.com/YOUR_USERNAME/edge-system-checker-web.git

# 프로젝트 디렉토리로 이동
cd edge-system-checker-web
```

### 2.3 Python 환경 설정

```bash
# backend 디렉토리로 이동
cd backend

# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2.4 환경 변수 설정

```bash
# .env 파일 생성
cp ../env.example .env

# .env 파일 편집
nano .env
```

다음 항목들을 실제 값으로 수정:
```env
NAS_IP=192.168.10.30
NAS_USER=admin2k
NAS_PASSWORD="실제비밀번호"
CAMERA_BASE_IP=192.168.1
CAMERA_START_IP=101
# ... 기타 설정
```

저장: `Ctrl+O` → `Enter` → `Ctrl+X`

### 2.5 서버 실행

**방법 A: 테스트 실행 (포그라운드)**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

웹 브라우저에서 `http://10.1.10.128:8000` 접속

종료: `Ctrl+C`

**방법 B: 백그라운드 실행**

```bash
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
```

로그 확인: `tail -f app.log`

**방법 C: systemd 서비스 등록 (권장)**

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/edge-checker-web.service
```

다음 내용 입력:

```ini
[Unit]
Description=Edge System Checker Web
After=network.target

[Service]
Type=simple
User=koast-user
WorkingDirectory=/home/koast-user/edge-system-checker-web/backend
Environment="PATH=/home/koast-user/edge-system-checker-web/backend/venv/bin"
ExecStart=/home/koast-user/edge-system-checker-web/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

저장 후:

```bash
# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl start edge-checker-web
sudo systemctl enable edge-checker-web

# 상태 확인
sudo systemctl status edge-checker-web
```

## 3단계: 업데이트 방법

코드를 수정한 후 재배포:

### 로컬에서:

```powershell
cd E:\cursor\edge-system-checker-web
git add .
git commit -m "업데이트 내용"
git push origin main
```

### 서버에서:

```bash
# 서버 접속
ssh koast-user@10.1.10.128

# 프로젝트 디렉토리로 이동
cd ~/edge-system-checker-web

# 최신 코드 가져오기
git pull origin main

# 서비스 재시작 (systemd 사용 시)
sudo systemctl restart edge-checker-web

# 또는 수동 실행 중이면 프로세스 종료 후 재시작
```

## 자주 사용하는 명령어

### 서버 관리

```bash
# 서비스 시작
sudo systemctl start edge-checker-web

# 서비스 중지
sudo systemctl stop edge-checker-web

# 서비스 재시작
sudo systemctl restart edge-checker-web

# 서비스 상태 확인
sudo systemctl status edge-checker-web

# 로그 확인
sudo journalctl -u edge-checker-web -f

# 코드 업데이트
cd ~/edge-system-checker-web
git pull origin main
sudo systemctl restart edge-checker-web
```

### 웹 접속

```
http://10.1.10.128:8000
```

## 문제 해결

### Git 인증 오류

GitHub에서 Personal Access Token 생성 필요

### 포트가 이미 사용 중

```bash
# 사용 중인 프로세스 확인
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 서비스 시작 실패

```bash
# 로그 확인
sudo journalctl -u edge-checker-web -n 50

# 수동으로 실행해서 오류 확인
cd ~/edge-system-checker-web/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 요약

1. **로컬**: GitHub에 push
2. **서버**: `git clone` → 환경 설정 → 실행
3. **업데이트**: 로컬에서 push → 서버에서 `git pull` → 재시작

이 방법이 훨씬 간단하고 효율적입니다! 🚀

