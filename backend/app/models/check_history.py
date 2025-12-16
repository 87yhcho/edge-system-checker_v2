"""
점검 이력 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import json


class CheckHistory(Base):
    """점검 이력 테이블"""
    __tablename__ = "check_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    check_type = Column(String(50), nullable=False, index=True)  # ups, camera, nas, system, all
    status = Column(String(20), nullable=False, index=True)  # PASS, FAIL, ERROR, SKIP
    results = Column(JSON, nullable=True)  # 점검 결과 상세 정보
    error_message = Column(Text, nullable=True)  # 에러 메시지
    duration_seconds = Column(Integer, nullable=True)  # 점검 소요 시간 (초)
    camera_count = Column(Integer, nullable=True)  # 카메라 개수 (카메라 점검인 경우)
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "check_type": self.check_type,
            "status": self.status,
            "results": self.results,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "camera_count": self.camera_count
        }

