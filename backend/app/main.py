"""
FastAPI 메인 애플리케이션
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api import checks, history, config
from app.core.websocket import manager
from app.services.scheduler import scheduler_service

# 로거 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("애플리케이션 시작 중...")
    
    # 데이터베이스 초기화
    await init_db()
    logger.info("데이터베이스 초기화 완료")
    
    # 스케줄러 시작
    if settings.SCHEDULER_ENABLED:
        scheduler_service.start()
        logger.info("스케줄러 시작됨")
    
    yield
    
    # 종료 시
    logger.info("애플리케이션 종료 중...")
    
    # 스케줄러 종료
    if settings.SCHEDULER_ENABLED:
        scheduler_service.shutdown()
        logger.info("스케줄러 종료됨")
    
    # WebSocket 연결 종료
    for connection in list(manager.active_connections):
        manager.disconnect(connection)
    logger.info("모든 WebSocket 연결 종료됨")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(checks.router, prefix="/api/checks", tags=["checks"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

# 정적 파일 제공 (프론트엔드)
try:
    import os
    # backend/app/main.py에서 frontend까지의 경로
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    project_root = os.path.dirname(backend_dir)
    frontend_path = os.path.join(project_root, "frontend")
    
    if os.path.exists(frontend_path):
        static_path = os.path.join(frontend_path, "static")
        if os.path.exists(static_path):
            app.mount("/static", StaticFiles(directory=static_path), name="static")
        
        @app.get("/")
        async def read_root():
            """메인 페이지"""
            index_path = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"message": "Frontend files not found"}
        
        @app.get("/history")
        async def read_history():
            """이력 페이지"""
            history_path = os.path.join(frontend_path, "history.html")
            if os.path.exists(history_path):
                return FileResponse(history_path)
            return {"message": "Frontend files not found"}
    else:
        logger.warning(f"프론트엔드 디렉토리를 찾을 수 없습니다: {frontend_path}")
except Exception as e:
    logger.warning(f"프론트엔드 파일 마운트 실패: {e}")


@app.get("/api/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "active_websocket_connections": len(manager.active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

