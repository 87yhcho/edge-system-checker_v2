"""
점검 실행 API 엔드포인트
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import logging

from app.core.database import get_db
from app.core.websocket import manager
from app.services.check_runner import check_runner
from app.schemas.check import CheckRunRequest, CheckStatusResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/run")
async def run_checks(
    request: CheckRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    점검 실행
    
    Args:
        request: 점검 실행 요청
        background_tasks: 백그라운드 작업
        db: 데이터베이스 세션
    
    Returns:
        점검 시작 확인 메시지
    """
    if check_runner.is_running:
        raise HTTPException(status_code=400, detail="점검이 이미 실행 중입니다.")
    
    # 백그라운드에서 점검 실행
    background_tasks.add_task(
        check_runner.run_all_checks,
        db=db,
        selected_checks=request.checks,
        camera_count=request.camera_count,
        auto_mode=request.auto_mode
    )
    
    return {
        "message": "점검이 시작되었습니다.",
        "checks": request.checks or ["ups", "camera", "nas", "system"],
        "camera_count": request.camera_count
    }


@router.get("/status")
async def get_check_status():
    """
    현재 점검 상태 조회
    
    Returns:
        점검 상태 정보
    """
    return CheckStatusResponse(
        is_running=check_runner.is_running,
        current_check=check_runner.current_check
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 연결 엔드포인트
    실시간 점검 진행 상황을 수신
    """
    await manager.connect(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (필요시)
            data = await websocket.receive_text()
            logger.debug(f"WebSocket 메시지 수신: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket 연결 해제됨")

