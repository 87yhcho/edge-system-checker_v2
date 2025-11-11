# Edge 시스템 종합 점검 도구

Edge 시스템(UPS, 카메라, NAS, 시스템)을 자동으로 점검하는 Python CLI 도구입니다.

## 🎯 주요 기능

### 1. UPS/NUT 상태 점검
- NUT 서비스 상태 확인 (nut-driver, nut-server, nut-monitor)
- 3493 포트 리스닝 확인
- UPS 상태 정보 조회 (배터리, 전압, 부하 등)
- NAS의 UPS 연결 상태 확인

### 2. 카메라 RTSP 연결 점검
- **GUI 모드**: 영상을 보면서 수동으로 판정
- **Auto 모드**: SSH 원격 실행, 자동으로 스트림 상태 검증
- 원본 카메라 영상 확인
- 블러 처리된 MediaMTX 스트리밍 확인
- 카메라 로그 파일 자동 분석
- 영상 파일 저장 상태 확인

### 3. NAS 상태 점검
- SSH 연결 확인
- 디스크 사용량 확인
- RAID 상태 확인
- 마운트 포인트 확인
- UPS 연결 상태 확인

### 4. 시스템 종합 점검
- OS 설정 (타임존, 로케일, 인코딩)
- 서비스 상태 (Tomcat, PostgreSQL, NUT 등)
- 포트 리스닝 (80, 5432, 3493)
- Java 설정 (버전, Heap 설정)
- 네트워크 설정 (IP 주소, 활성 연결)
- 디스크 공간 확인
- Cron 작업 확인

## 📋 점검 항목 및 PASS/FAIL 조건

### 1️⃣ UPS/NUT 상태 점검

| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **NUT 서비스** | • nut-driver@ups.service: active<br>• nut-server.service: active<br>• nut-monitor.service: active | • 서비스 중 하나라도 inactive 또는 failed |
| **포트 리스닝** | • 3493 포트가 리스닝 중 | • 3493 포트가 리스닝 안 됨 |
| **UPS 상태** | • `upsc ups@localhost` 명령 성공<br>• ups.status 조회 가능<br>• battery.charge 조회 가능 | • UPS 연결 실패<br>• 상태 정보 조회 불가 |
| **NAS 연결** | • NAS에서 `upsc ups@localhost` 성공<br>• NAS가 UPS 모니터링 중 | • NAS에서 UPS 연결 실패<br>• 모니터링 안 됨 |

**전체 판정:** 모든 항목이 PASS여야 전체 PASS

---

### 2️⃣ 카메라 RTSP 연결 점검

#### 원본 카메라 스트림
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **RTSP 연결** | • `rtsp://IP:554/cam0_0` 연결 성공<br>• 5초 이내 응답 | • 연결 실패 (타임아웃)<br>• 5초 초과 |
| **프레임 읽기** | • 첫 프레임 읽기 성공<br>• 해상도 정보 획득 | • 프레임 읽기 실패<br>• 해상도 0x0 |
| **GUI 모드** | • 사용자가 영상 확인 후 PASS 입력 | • 사용자가 FAIL 입력 |
| **Auto 모드** | • 프레임 읽기 성공 (자동 PASS) | • 프레임 읽기 실패 (자동 FAIL) |

#### 블러 처리 스트림 (MediaMTX)
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **RTSP 연결** | • `rtsp://127.0.0.1:PORT/live` 연결 성공<br>• 포트: 1111, 1112, 1113... | • 연결 실패<br>• MediaMTX 미작동 |
| **프레임 읽기** | • 블러 처리된 프레임 읽기 성공 | • 프레임 읽기 실패 |

#### 카메라 로그 점검
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **로그 파일** | • `/home/.../logs/YYYY/MM/DD/rtsp_streamN_YYYYMMDD.log` 존재 | • 로그 파일 없음 |
| **타임스탬프** | • 최근 10분 이내 로그 | • 10분 이상 오래된 로그 |
| **프레임 수** | • 4400 ~ 4600 프레임 | • 범위 밖 |
| **영상 길이** | • 280 ~ 310초 | • 범위 밖 |

#### 영상 파일 점검
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **파일 존재** | • `/home/.../cam/YYYY/MM/DD/HH/` 경로에 mp4 파일 존재 | • 파일 없음 |
| **타임스탬프** | • 최근 10분 이내 파일 | • 10분 이상 오래된 파일 |
| **모든 카메라** | • 모든 카메라의 영상 파일 존재 | • 하나라도 없음 |

**전체 판정:** 모든 카메라의 원본/블러/로그가 모두 PASS여야 전체 PASS

---

### 3️⃣ NAS 상태 점검

| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **SSH 연결** | • NAS IP:PORT로 SSH 연결 성공 | • SSH 연결 실패<br>• 인증 실패 |
| **디스크 사용량** | • `df -h` 명령 성공<br>• 디스크 정보 획득 | • 명령 실패<br>• 디스크 정보 없음 |
| **RAID 상태** | • `/proc/mdstat` 읽기 성공<br>• RAID 배열 정상 | • 파일 읽기 실패<br>• RAID 오류 |
| **마운트 포인트** | • `/mnt/nas` 마운트 확인<br>• `ls -la` 성공 | • 마운트 안 됨<br>• 접근 불가 |
| **UPS 연결** | • `upsc ups@localhost` 또는 `synoups --status` 성공 | • UPS 상태 확인 불가 |

**전체 판정:** SSH 연결과 주요 정보 획득 성공 시 PASS

---

### 4️⃣ 시스템 종합 점검

#### OS 설정
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **타임존** | • 타임존 설정됨 (예: Asia/Seoul) | • 타임존 미설정 |
| **로케일** | • 로케일 설정됨 (예: ko_KR.UTF-8) | • 로케일 미설정 |
| **인코딩** | • UTF-8 인코딩 | • 다른 인코딩 |

#### 서비스 상태
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **Tomcat** | • active (running) | • inactive, failed, dead |
| **PostgreSQL** | • active (running) | • inactive, failed, dead |
| **NUT Server** | • active (running) | • inactive, failed, dead |
| **NUT Monitor** | • active (running) | • inactive, failed, dead |
| **Stream** | • active (running) | • inactive, failed, dead |

#### 포트 리스닝
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **HTTP (80)** | • `ss -tlnp` 에서 80 포트 확인 | • 포트 리스닝 안 됨 |
| **PostgreSQL (5432)** | • 5432 포트 리스닝 | • 포트 리스닝 안 됨 |
| **NUT (3493)** | • 3493 포트 리스닝 | • 포트 리스닝 안 됨 |

#### Java 설정
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **Java 버전** | • Java 17 이상 | • Java 17 미만 (WARN)<br>• Java 없음 (FAIL) |
| **Heap 설정** | • -Xms, -Xmx 옵션 확인됨 | • Heap 설정 없음 (WARN) |

#### 네트워크 설정
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **IP 주소** | • `192.168.1.10/24` 존재<br>• `192.168.10.20/24` 존재<br>• **두 개 모두 필수** | • 필수 IP 중 하나라도 없음 |
| **활성 연결** | • `nmcli` 에서 활성 연결 확인 | • 활성 연결 없음 |

#### 디스크 공간
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **루트 파티션** | • 사용률 80% 미만 | • 사용률 80% 이상 (WARN)<br>• 사용률 90% 이상 (FAIL) |
| **PostgreSQL** | • 데이터 디렉토리 접근 가능 | • 접근 불가 (SKIP) |

#### Cron 작업
| 점검 항목 | PASS 조건 | FAIL 조건 |
|----------|----------|----------|
| **Crontab** | • `crontab -l` 성공 | • crontab 없음 (WARN) |
| **일일 동기화** | • `0 1 * * *` 형식의 스케줄 확인 | • 동기화 스케줄 없음 (WARN) |

**전체 판정:** FAIL이 하나라도 있으면 전체 FAIL, WARN은 경고만 표시

## 📦 설치 방법

### 방법 1: UV 사용 (권장) ⚡

#### 필수 요구사항
- Ubuntu/Debian Linux
- Python 3.11 이상
- Internet connection

#### 자동 설치 스크립트
```bash
# 저장소 클론
git clone https://github.com/87yhcho/edge-system-checker.git
cd edge-system-checker

# 설치 스크립트 실행 (UV 자동 설치)
chmod +x INSTALL_PACKAGES.sh
./INSTALL_PACKAGES.sh

# ⚠️ 중요: 터미널 재시작 (UV PATH 적용)
exit
# 다시 SSH 접속

# 환경 변수 설정
cd edge-system-checker
cp env.example .env
nano .env  # 실제 값으로 수정

# 실행
./run_edge_checker.sh
```

#### 수동 설치
```bash
# UV 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# PATH 설정 (중요!)
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# 터미널 재시작 또는 bashrc 로드
source ~/.bashrc

# UV 설치 확인
uv --version

# 시스템 의존성
sudo apt update
sudo apt install -y python3 python3-dev libopencv-dev libpq-dev

# 환경 변수 설정
cp env.example .env
nano .env

# 실행
uv run checker.py
```

### 방법 2: 기존 pip/venv 방식 (호환성 유지)

```bash
# 저장소 클론
git clone https://github.com/87yhcho/edge-system-checker.git
cd edge-system-checker

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp env.example .env
nano .env

# 실행
python checker.py
```

## 🚀 사용 방법

### UV로 실행 (권장)
```bash
./run_edge_checker.sh    # UV 자동 설치 + 실행
# 또는
uv run checker.py         # 직접 실행
```

### 기존 방식으로 실행
```bash
python3 checker.py
```

### 카메라 점검 모드 선택
- **GUI 모드 (1)**: 장비에서 직접 실행, 영상 확인
- **Auto 모드 (2)**: SSH 원격 실행, 자동 검증 (기본값)

### 점검 흐름
1. 카메라 개수 입력
2. [1/4] UPS/NUT 상태 점검
3. [2/4] 카메라 RTSP 연결 점검
4. [3/4] NAS 상태 점검
5. [4/4] 시스템 종합 점검
6. 최종 리포트 생성 (`report_YYYY-MM-DD_HH-MM-SS.txt`)

## 📊 출력 예시

```
════════════════════════════════════════════════════════════════════════════════
  전체 요약
════════════════════════════════════════════════════════════════════════════════
  UPS/NUT              : ✓ PASS
  카메라                : ✓ PASS
  NAS                  : ✓ PASS
  시스템                : ✓ PASS
════════════════════════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════════════════════════
  카메라 상세 결과
════════════════════════════════════════════════════════════════════════════════
  카메라       IP                원본       블러       로그      
  카메라 1     192.168.1.101     PASS       PASS       PASS      
  카메라 2     192.168.1.102     PASS       PASS       PASS      
  카메라 3     192.168.1.103     PASS       PASS       PASS      
  카메라 4     192.168.1.104     PASS       PASS       PASS      
════════════════════════════════════════════════════════════════════════════════
```

## 📁 프로젝트 구조

```
edge-system-checker/
├── checker.py              # 메인 실행 파일
├── requirements.txt        # Python 의존성
├── env.example            # 환경 변수 템플릿
├── checks/                # 점검 모듈
│   ├── __init__.py
│   ├── ups_check.py       # UPS/NUT 점검
│   ├── camera_check.py    # 카메라 점검
│   ├── nas_check.py       # NAS 점검
│   └── system_check.py    # 시스템 점검
└── utils/                 # 유틸리티
    ├── __init__.py
    ├── ui.py             # CLI UI (색상, 출력)
    └── reporter.py       # 리포트 생성
```

## ⚙️ 환경 변수

`.env` 파일 설정 예시:

```env
# NUT/UPS
NUT_UPS_NAME=ups

# NAS
NAS_IP=192.168.10.30
NAS_USER=admin2k
NAS_PASSWORD=your_password
NAS_PORT=2222

# 카메라
CAMERA_BASE_IP=192.168.1
CAMERA_START_IP=101
CAMERA_USER=root
CAMERA_PASS=root
CAMERA_RTSP_PATH=cam0_0
CAMERA_RTSP_PORT=554
CAMERA_MEDIAMTX_BASE_PORT=1111
```

## 🔧 주요 기능 상세

### IP 주소 필수 체크
- `192.168.1.10/24`와 `192.168.10.20/24` 필수
- 두 개 모두 있어야 PASS
- 하나라도 누락 시 FAIL 및 상세 정보 표시

### 카메라 로그 분석
- 로그 파일 자동 검색 (최근 10일)
- 프레임 수: 4400~4600 체크
- 영상 길이: 280~310초 체크
- 타임스탬프: 10분 이내 체크

### 영상 파일 존재 확인
- 시간대별 폴더 자동 검색
- 최근 10분 이내 파일 확인
- 모든 카메라 파일 존재 여부 확인

### 한글 문자 정렬
- 터미널에서 한글 문자 너비(2칸) 정확히 계산
- ANSI 색상 코드 고려한 정렬
- 모든 테이블 완벽한 정렬

## 🐛 트러블슈팅

### Git 관련

#### Git Pull 충돌 해결
```bash
# 로컬 변경사항이 있어서 pull이 실패할 때
cd ~/edge-system-checker

# 방법 1: 로컬 변경사항 버리고 원격으로 덮어쓰기 (권장)
git restore .
git pull origin main

# 방법 2: 로컬 변경사항 임시 저장
git stash
git pull origin main
git stash pop  # 필요시 다시 적용

# 방법 3: 완전히 재설정 (선택사항)
rm -rf ~/edge-system-checker
git clone https://github.com/87yhcho/edge-system-checker.git
cd edge-system-checker
```

### UV 관련

#### UV 명령어를 찾을 수 없음 (`uv: command not found`)
```bash
# 원인: PATH가 설정되지 않음
# 해결 방법 1: PATH 수동 설정
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# 해결 방법 2: bashrc 다시 로드
source ~/.bashrc

# 해결 방법 3: 터미널 재시작
exit
# 다시 접속

# UV 확인
uv --version
```

#### UV 설치 실패
```bash
# 수동 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# PATH 설정
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# .bashrc에 영구 등록
echo 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### UV가 Python을 찾지 못함
```bash
# Python 버전 확인
python3 --version  # 3.11 이상이어야 함

# UV가 사용할 Python 지정
export UV_PYTHON=$(which python3)
```

#### INSTALL_PACKAGES.sh 실행 시 UV 오류
```bash
# 스크립트 실행 후 터미널 재시작 필요
./INSTALL_PACKAGES.sh

# 터미널 재시작
exit
# 다시 접속

# UV 작동 확인
uv --version

# 프로그램 실행
./run_edge_checker.sh
```

### 전통적 pip/venv 방식

#### NumPy 호환성 문제
```bash
pip install "numpy<2.0"
```

#### pip 설치 권한 오류
```bash
# 가상환경 사용
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 기타

#### OpenCV 비디오 에러 메시지
- H.264, HEVC 디코딩 경고는 정상 현상
- 이미 로그 레벨 설정으로 숨겨져 있음

#### SSH 연결 실패
- NAS IP, 포트, 계정 정보 확인
- 방화벽 설정 확인

#### 시스템 패키지 부족
```bash
# OpenCV, PostgreSQL 라이브러리 설치
sudo apt install -y libopencv-dev libpq-dev
```

## 📝 라이센스

MIT License

## 👤 작성자

- 프로젝트 생성일: 2025-10-27
- Python 3.11+
- 대상 시스템: Edge 장비 (Ubuntu/Debian)

## 🎉 업데이트 내역

- **2025-01-29**: UV 기반 배포로 전환 ⚡
  - UV 패키지 관리 시스템 도입
  - pip 대비 10-100배 빠른 의존성 해결
  - pyproject.toml 추가
  - 자동 UV 설치 스크립트
  - 기존 pip/venv 방식 호환성 유지

- **2025-10-27**: 초기 릴리스
  - UPS/NUT 점검
  - 카메라 RTSP 점검 (GUI/Auto 모드)
  - NAS 점검
  - 시스템 종합 점검
  - 한글 문자 정렬 지원
  - IP 주소 필수 체크
  - 비디오 에러 메시지 완전 숨김
