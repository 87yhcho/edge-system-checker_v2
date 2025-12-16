"""
점검 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class CheckRunRequest(BaseModel):
    """점검 실행 요청"""
    checks: Optional[List[str]] = None  # None이면 모두 실행
    camera_count: int = 4
    auto_mode: bool = True


class CheckStatusResponse(BaseModel):
    """점검 상태 응답"""
    is_running: bool
    current_check: Optional[str] = None
    progress: Optional[int] = None


class CheckHistoryResponse(BaseModel):
    """점검 이력 응답"""
    id: int
    timestamp: datetime
    check_type: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None
    camera_count: Optional[int] = None
    
    model_config = {"from_attributes": True}


class CheckHistoryListResponse(BaseModel):
    """점검 이력 목록 응답"""
    total: int
    items: List[CheckHistoryResponse]
    page: int
    page_size: int


class ConfigResponse(BaseModel):
    """설정 응답"""
    camera_count: int
    auto_mode: bool
    scheduler_enabled: bool
    notification_enabled: bool

