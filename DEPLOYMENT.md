# 배포 가이드

이 문서는 Edge System Checker Web을 Git에 올리고 원격 서버에 배포하는 방법을 설명합니다.

## 1단계: Git 저장소 초기화 및 커밋

### 1.1 Git 저장소 초기화

```bash
cd E:\cursor\edge-system-checker-web
git init
```

### 1.2 .gitignore 확인

`.gitignore` 파일이 이미 생성되어 있습니다. 다음 항목들이 제외됩니다:
- Python 캐시 파일 (`__pycache__/`)
- 가상환경 (`venv/`, `env/`)
- 환경 변수 파일 (`.env`)
- 데이터베이스 파일 (`*.db`, `*.sqlite`)
- 로그 파일 (`*.log`)

### 1.3 파일 추가 및 커밋

```bash
# 모든 파일 추가
git add .

# 커밋 메시지와 함께 커밋
git commit -m "Initial commit: Edge System Checker Web version"
```

## 2단계: GitHub에 업로드

### 2.1 GitHub 저장소 생성

1. GitHub 웹사이트 (https://github.com)에 로그인
2. 우측 상단의 "+" 버튼 클릭 → "New repository" 선택
3. 저장소 이름 입력 (예: `edge-system-checker-web`)
4. "Create repository" 클릭

### 2.2 원격 저장소 연결 및 푸시

```bash
# 원격 저장소 추가 (YOUR_USERNAME과 REPO_NAME을 실제 값으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/edge-system-checker-web.git

# 또는 SSH 사용 시
git remote add origin git@github.com:YOUR_USERNAME/edge-system-checker-web.git

# 메인 브랜치로 이름 변경 (필요한 경우)
git branch -M main

# 원격 저장소에 푸시
git push -u origin main
```

**참고**: GitHub 인증이 필요합니다. Personal Access Token을 사용하거나 SSH 키를 설정해야 합니다.

## 3단계: 원격 서버에 배포

### 3.1 서버 접속 및 디렉토리 생성

```bash
# SSH로 서버 접속
ssh koast-user@10.1.10.128

# 프로젝트 디렉토리 생성
mkdir -p ~/edge-system-checker-web
cd ~/edge-system-checker-web
```

### 3.2 Git에서 코드 클론

**방법 A: GitHub에서 직접 클론 (권장)**

```bash
# 서버에서 실행
cd ~
git clone https://github.com/YOUR_USERNAME/edge-system-checker-web.git
cd edge-system-checker-web
```

**방법 B: 로컬에서 SCP로 전송**

```bash
# 로컬 컴퓨터에서 실행 (PowerShell)
cd E:\cursor
scp -r edge-system-checker-web koast-user@10.1.10.128:~/edge-system-checker-web
```

### 3.3 서버에서 환경 설정

```bash
# 서버에 접속한 상태에서
cd ~/edge-system-checker-web/backend

# Python 가상환경 생성 (Python 3.11 이상 필요)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 또는 UV 사용 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv pip install -r requirements.txt
```

### 3.4 환경 변수 설정

```bash
# 서버에서 실행
cd ~/edge-system-checker-web/backend
cp ../env.example .env

# .env 파일 편집
nano .env
# 또는
vi .env
```

`.env` 파일에서 다음 항목들을 실제 값으로 수정:
- `NAS_IP`, `NAS_USER`, `NAS_PASSWORD`
- `CAMERA_BASE_IP`, `CAMERA_START_IP` 등
- 기타 필요한 설정

### 3.5 서비스 실행

**개발 모드 (테스트용)**

```bash
cd ~/edge-system-checker-web/backend
source venv/bin/activate  # 가상환경 활성화
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**프로덕션 모드 (systemd 서비스로 등록)**

#### systemd 서비스 파일 생성

```bash
# 서버에서 실행
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

**서비스 시작**

```bash
# 서비스 파일 리로드
sudo systemctl daemon-reload

# 서비스 시작
sudo systemctl start edge-checker-web

# 서비스 상태 확인
sudo systemctl status edge-checker-web

# 부팅 시 자동 시작 설정
sudo systemctl enable edge-checker-web
```

### 3.6 방화벽 설정 (필요한 경우)

```bash
# 포트 8000 열기
sudo ufw allow 8000/tcp
# 또는
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## 4단계: 접속 확인

웹 브라우저에서 다음 주소로 접속:
```
http://10.1.10.128:8000
```

## 업데이트 방법

### 코드 업데이트 후 재배포

**로컬에서:**
```bash
cd E:\cursor\edge-system-checker-web
git add .
git commit -m "업데이트 내용 설명"
git push origin main
```

**서버에서:**
```bash
cd ~/edge-system-checker-web
git pull origin main

# 서비스 재시작
sudo systemctl restart edge-checker-web
```

## 트러블슈팅

### 서비스가 시작되지 않는 경우

```bash
# 로그 확인
sudo journalctl -u edge-checker-web -f

# 서비스 상태 확인
sudo systemctl status edge-checker-web
```

### 포트가 이미 사용 중인 경우

`.env` 파일에서 `PORT` 값을 변경하거나, systemd 서비스 파일의 `ExecStart`에서 포트 번호 변경

### 권한 오류

```bash
# 파일 소유권 확인
ls -la ~/edge-system-checker-web

# 필요시 소유권 변경
sudo chown -R koast-user:koast-user ~/edge-system-checker-web
```

## 보안 권장사항

1. **.env 파일 보호**: `.env` 파일에 민감한 정보가 포함되어 있으므로 Git에 올리지 않도록 주의
2. **방화벽 설정**: 필요한 포트만 열기
3. **HTTPS 사용**: 프로덕션 환경에서는 Nginx를 앞에 두고 HTTPS 사용 권장

## Nginx 리버스 프록시 설정 (선택사항)

프로덕션 환경에서 Nginx를 사용하여 HTTPS를 제공할 수 있습니다:

```nginx
server {
    listen 80;
    server_name 10.1.10.128;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 지원
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

