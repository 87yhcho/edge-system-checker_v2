"""
설정 관리 API 엔드포인트
"""
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.check import ConfigResponse

router = APIRouter()


@router.get("", response_model=ConfigResponse)
async def get_config():
    """
    현재 설정 조회
    
    Returns:
        현재 설정 정보
    """
    return ConfigResponse(
        camera_count=4,  # 기본값, 실제로는 설정에서 가져올 수 있음
        auto_mode=True,
        scheduler_enabled=settings.SCHEDULER_ENABLED,
        notification_enabled=settings.NOTIFICATION_ENABLED
    )

