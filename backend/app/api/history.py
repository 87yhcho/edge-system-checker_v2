"""
점검 이력 조회 API 엔드포인트
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.check_history import CheckHistory
from app.schemas.check import CheckHistoryResponse, CheckHistoryListResponse

router = APIRouter()


@router.get("", response_model=CheckHistoryListResponse)
async def get_check_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    check_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    점검 이력 목록 조회 (페이지네이션)
    
    Args:
        page: 페이지 번호
        page_size: 페이지 크기
        check_type: 점검 종류 필터
        status: 상태 필터
        db: 데이터베이스 세션
    
    Returns:
        점검 이력 목록
    """
    # 쿼리 빌드
    query = select(CheckHistory)
    count_query = select(func.count(CheckHistory.id))
    
    # 필터 적용
    if check_type:
        query = query.where(CheckHistory.check_type == check_type)
        count_query = count_query.where(CheckHistory.check_type == check_type)
    
    if status:
        query = query.where(CheckHistory.status == status)
        count_query = count_query.where(CheckHistory.status == status)
    
    # 정렬 및 페이지네이션
    query = query.order_by(desc(CheckHistory.timestamp))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 실행
    result = await db.execute(query)
    items = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return CheckHistoryListResponse(
        total=total,
        items=[CheckHistoryResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size
    )


@router.get("/{history_id}", response_model=CheckHistoryResponse)
async def get_check_history_detail(
    history_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 점검 이력 상세 조회
    
    Args:
        history_id: 점검 이력 ID
        db: 데이터베이스 세션
    
    Returns:
        점검 이력 상세 정보
    """
    query = select(CheckHistory).where(CheckHistory.id == history_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="점검 이력을 찾을 수 없습니다.")
    
    return CheckHistoryResponse.model_validate(item)

