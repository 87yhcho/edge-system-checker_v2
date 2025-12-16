# Edge System Checker Web

Edge 시스템 점검 도구의 웹 버전입니다. 기존 CLI 도구의 모든 기능을 웹 인터페이스로 제공합니다.

## 주요 기능

- ✅ **실시간 점검 모니터링**: WebSocket을 통한 실시간 점검 진행 상황 표시
- ✅ **점검 이력 관리**: SQLite 데이터베이스에 점검 이력 저장 및 조회
- ✅ **주기적 자동 점검**: APScheduler를 사용한 스케줄링
- ✅ **알림 기능**: 이메일 및 슬랙 알림 발송
- ✅ **웹 대시보드**: 직관적인 웹 인터페이스

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd edge-system-checker-web
```

### 2. 백엔드 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

또는 UV 사용:

```bash
cd backend
uv pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
cp env.example backend/.env
# backend/.env 파일을 편집하여 실제 값으로 수정
```

### 4. 서버 실행

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 웹 브라우저 접속

```
http://localhost:8000
```

## 프로젝트 구조

```
edge-system-checker-web/
├── backend/                 # FastAPI 백엔드
│   ├── app/                 # 애플리케이션 코드
│   ├── checks/              # 점검 모듈 (기존)
│   ├── utils/               # 유틸리티 (기존)
│   └── requirements.txt     # Python 의존성
├── frontend/                # 웹 프론트엔드
│   ├── index.html           # 메인 대시보드
│   ├── history.html         # 이력 조회 페이지
│   └── static/              # 정적 파일
│       ├── css/
│       └── js/
└── env.example              # 환경 변수 템플릿
```

## 사용 방법

### 대시보드

1. 웹 브라우저에서 `http://localhost:8000` 접속
2. 점검 항목 선택 (UPS/NUT, 카메라, NAS, 시스템)
3. 카메라 개수 및 모드 설정
4. "점검 시작" 버튼 클릭
5. 실시간으로 점검 진행 상황 확인

### 이력 조회

1. "이력 조회" 메뉴 클릭
2. 필터 설정 (점검 종류, 상태)
3. 상세 결과 확인

## API 문서

FastAPI 자동 생성 문서:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 주요 API 엔드포인트

- `POST /api/checks/run` - 점검 실행
- `GET /api/checks/status` - 점검 상태 조회
- `WebSocket /api/checks/ws` - 실시간 점검 진행 상황
- `GET /api/history` - 점검 이력 조회
- `GET /api/history/{id}` - 점검 이력 상세 조회

## 환경 변수

자세한 환경 변수 설정은 `env.example` 파일을 참조하세요.

주요 설정:
- `HOST`, `PORT`: 웹 서버 설정
- `DATABASE_URL`: 데이터베이스 연결 URL
- `SCHEDULER_ENABLED`: 스케줄러 활성화 여부
- `NOTIFICATION_ENABLED`: 알림 활성화 여부
- 기존 점검 관련 설정 (UPS, 카메라, NAS 등)

## 스케줄러 설정

`.env` 파일에서 스케줄러 설정:

```env
SCHEDULER_ENABLED=True
SCHEDULER_CRON_HOUR=1    # 매일 새벽 1시
SCHEDULER_CRON_MINUTE=0
```

## 알림 설정

### 이메일 알림

```env
NOTIFICATION_EMAIL_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password
SMTP_FROM=your_email@gmail.com
SMTP_TO=recipient@example.com
```

### 슬랙 알림

```env
NOTIFICATION_SLACK_ENABLED=True
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 트러블슈팅

### 포트가 이미 사용 중인 경우

`.env` 파일에서 `PORT` 값을 변경하거나 다른 포트로 실행:

```bash
uvicorn app.main:app --port 8001
```

### 데이터베이스 오류

데이터베이스 파일 권한 확인:

```bash
chmod 666 backend/check_history.db
```

### WebSocket 연결 실패

방화벽 설정 확인 및 CORS 설정 확인

## 기존 CLI 도구와의 관계

이 웹 버전은 기존 `edge-system-checker-v2` CLI 도구의 모든 기능을 웹 인터페이스로 제공합니다. 기존 CLI 도구는 그대로 유지되며, 웹 버전은 별도로 실행됩니다.

## 라이센스

MIT License

## 작성자

- 프로젝트 생성일: 2025-12-16
- Python 3.11+
- FastAPI 0.104+
