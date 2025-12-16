# 빠른 배포 가이드 (초보자용)

이 가이드는 초보자도 쉽게 따라할 수 있도록 단계별로 설명합니다.

## 준비물

- Git 설치 (https://git-scm.com/downloads)
- GitHub 계정 (https://github.com)
- SSH 접속 가능한 원격 서버 (10.1.10.128)

## 방법 1: 자동 배포 스크립트 사용 (가장 쉬움)

### Windows 사용자

1. PowerShell을 관리자 권한으로 실행
2. 프로젝트 폴더로 이동:
   ```powershell
   cd E:\cursor\edge-system-checker-web
   ```
3. 배포 스크립트 실행:
   ```powershell
   .\deploy.ps1
   ```
4. 스크립트가 안내하는 대로 진행

### Linux/Mac 사용자

1. 터미널 열기
2. 프로젝트 폴더로 이동:
   ```bash
   cd ~/edge-system-checker-web
   ```
3. 배포 스크립트 실행 권한 부여:
   ```bash
   chmod +x deploy.sh
   ```
4. 배포 스크립트 실행:
   ```bash
   ./deploy.sh
   ```

## 방법 2: 수동 배포 (단계별)

### 1단계: Git에 올리기

#### 1.1 Git 저장소 초기화

PowerShell 또는 터미널에서:

```bash
cd E:\cursor\edge-system-checker-web
git init
```

#### 1.2 파일 추가 및 커밋

```bash
git add .
git commit -m "Initial commit: Edge System Checker Web"
```

#### 1.3 GitHub에 저장소 생성

1. 브라우저에서 https://github.com 접속
2. 로그인
3. 우측 상단 "+" 버튼 클릭 → "New repository"
4. 저장소 이름 입력: `edge-system-checker-web`
5. "Create repository" 클릭

#### 1.4 GitHub에 업로드

GitHub에서 생성된 저장소 페이지에서 나온 명령어를 사용하거나:

```bash
# 원격 저장소 추가 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/edge-system-checker-web.git

# 브랜치 이름을 main으로 설정
git branch -M main

# 업로드
git push -u origin main
```

**주의**: GitHub 인증이 필요합니다. Personal Access Token을 사용하세요.

### 2단계: 서버에 배포

#### 2.1 서버 접속

```bash
ssh koast-user@10.1.10.128
```

#### 2.2 프로젝트 디렉토리 생성

```bash
mkdir -p ~/edge-system-checker-web
cd ~/edge-system-checker-web
```

#### 2.3 GitHub에서 코드 다운로드

**방법 A: GitHub에서 직접 클론 (권장)**

```bash
# GitHub 저장소 URL을 사용
git clone https://github.com/YOUR_USERNAME/edge-system-checker-web.git
cd edge-system-checker-web
```

**방법 B: 로컬에서 파일 전송**

로컬 컴퓨터에서 (PowerShell):

```bash
# 압축 파일 생성
cd E:\cursor
tar -czf edge-system-checker-web.tar.gz edge-system-checker-web

# 서버로 전송
scp edge-system-checker-web.tar.gz koast-user@10.1.10.128:~/

# 서버에서 압축 해제
ssh koast-user@10.1.10.128
cd ~
tar -xzf edge-system-checker-web.tar.gz
rm edge-system-checker-web.tar.gz
```

#### 2.4 Python 환경 설정

```bash
# 서버에서 실행
cd ~/edge-system-checker-web/backend

# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

#### 2.5 환경 변수 설정

```bash
# .env 파일 생성
cp ../env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일에서 다음 항목들을 실제 값으로 수정:
- `NAS_IP=192.168.10.30` (실제 NAS IP)
- `NAS_USER=admin2k` (실제 사용자명)
- `NAS_PASSWORD="실제비밀번호"` (실제 비밀번호)
- 기타 필요한 설정

저장: `Ctrl+O`, `Enter`, `Ctrl+X`

#### 2.6 서버 실행

**테스트 실행:**

```bash
cd ~/edge-system-checker-web/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**백그라운드 실행 (nohup 사용):**

```bash
cd ~/edge-system-checker-web/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
```

#### 2.7 접속 확인

웹 브라우저에서:
```
http://10.1.10.128:8000
```

## 방법 3: systemd 서비스로 등록 (프로덕션)

서버를 재시작해도 자동으로 실행되도록 설정:

### 3.1 서비스 파일 생성

```bash
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

### 3.2 서비스 시작

```bash
# 서비스 파일 리로드
sudo systemctl daemon-reload

# 서비스 시작
sudo systemctl start edge-checker-web

# 서비스 상태 확인
sudo systemctl status edge-checker-web

# 부팅 시 자동 시작
sudo systemctl enable edge-checker-web
```

### 3.3 서비스 관리 명령어

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
```

## 업데이트 방법

### 코드 수정 후 재배포

**로컬에서:**

```bash
cd E:\cursor\edge-system-checker-web
git add .
git commit -m "업데이트 내용"
git push origin main
```

**서버에서:**

```bash
cd ~/edge-system-checker-web
git pull origin main

# 서비스 재시작
sudo systemctl restart edge-checker-web
```

## 문제 해결

### 1. Git 인증 오류

GitHub Personal Access Token 생성:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 권한 선택: `repo` 체크
4. 토큰 복사
5. Git 명령어 실행 시 비밀번호 대신 토큰 사용

### 2. 서버 접속 오류

```bash
# SSH 키 생성 (로컬에서)
ssh-keygen -t rsa -b 4096

# 공개키를 서버에 복사
ssh-copy-id koast-user@10.1.10.128
```

### 3. 포트가 이미 사용 중

```bash
# 사용 중인 포트 확인
sudo netstat -tulpn | grep 8000

# 또는
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 4. 서비스가 시작되지 않음

```bash
# 로그 확인
sudo journalctl -u edge-checker-web -n 50

# 서비스 파일 경로 확인
sudo systemctl cat edge-checker-web
```

## 도움이 필요하신가요?

문제가 발생하면 다음을 확인하세요:
1. Python 버전: `python3 --version` (3.11 이상 필요)
2. 포트 방화벽: `sudo ufw status`
3. 서비스 로그: `sudo journalctl -u edge-checker-web -f`

