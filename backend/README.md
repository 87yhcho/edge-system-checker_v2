# Edge System Checker Web - 백엔드

Edge 시스템 점검 도구의 웹 버전 백엔드입니다.

## 설치 방법

### 1. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

또는 UV 사용:

```bash
cd backend
uv pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cp ../env.example .env
# .env 파일을 편집하여 실제 값으로 수정
```

### 3. 데이터베이스 초기화

애플리케이션 실행 시 자동으로 데이터베이스가 초기화됩니다.

## 실행 방법

### 개발 모드

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 모드

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 엔드포인트

### 점검 실행
- `POST /api/checks/run` - 점검 실행
- `GET /api/checks/status` - 점검 상태 조회
- `WebSocket /api/checks/ws` - 실시간 점검 진행 상황

### 이력 조회
- `GET /api/history` - 점검 이력 목록 조회
- `GET /api/history/{id}` - 점검 이력 상세 조회

### 설정
- `GET /api/config` - 현재 설정 조회

### 헬스 체크
- `GET /api/health` - 서버 상태 확인

## API 문서

FastAPI 자동 생성 문서:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 애플리케이션
│   ├── api/                 # REST API 엔드포인트
│   │   ├── checks.py        # 점검 실행 API
│   │   ├── history.py       # 이력 조회 API
│   │   └── config.py         # 설정 API
│   ├── core/                # 핵심 설정
│   │   ├── config.py        # 애플리케이션 설정
│   │   ├── database.py      # 데이터베이스 연결
│   │   └── websocket.py     # WebSocket 관리
│   ├── models/              # 데이터베이스 모델
│   │   └── check_history.py # 점검 이력 모델
│   ├── services/            # 비즈니스 로직
│   │   ├── check_runner.py  # 점검 실행 서비스
│   │   ├── scheduler.py     # 스케줄러 서비스
│   │   └── notifier.py      # 알림 서비스
│   └── schemas/             # Pydantic 스키마
│       └── check.py         # 점검 관련 스키마
├── checks/                  # 기존 점검 모듈
│   ├── ups_check.py
│   ├── camera_check.py
│   ├── nas_check.py
│   └── system_check.py
├── utils/                   # 유틸리티
│   ├── logger.py
│   └── reporter.py
└── requirements.txt         # Python 의존성
```

## 주요 기능

1. **점검 실행**: UPS, 카메라, NAS, 시스템 점검 실행
2. **실시간 모니터링**: WebSocket을 통한 실시간 점검 진행 상황 전송
3. **이력 관리**: SQLite 데이터베이스에 점검 이력 저장 및 조회
4. **스케줄러**: APScheduler를 사용한 주기적 자동 점검
5. **알림**: 이메일 및 슬랙 알림 발송

## 환경 변수

자세한 환경 변수 설정은 `env.example` 파일을 참조하세요.

## 라이센스

MIT License

