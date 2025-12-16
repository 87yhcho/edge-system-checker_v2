"""
WebSocket 연결 관리
"""
from typing import Set
from fastapi import WebSocket
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """클라이언트 연결"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket 연결됨. 총 연결 수: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 해제"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket 연결 해제됨. 총 연결 수: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """특정 클라이언트에게 메시지 전송"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """모든 연결된 클라이언트에게 브로드캐스트"""
        # datetime 객체를 문자열로 변환하는 재귀 함수
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            return obj
        
        # 메시지를 직렬화 가능하게 변환
        try:
            serialized_message = serialize_datetime(message)
        except Exception as e:
            logger.error(f"메시지 직렬화 실패: {e}")
            return
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(serialized_message)
            except Exception as e:
                logger.error(f"브로드캐스트 실패: {e}")
                disconnected.add(connection)
        
        # 연결이 끊어진 클라이언트 제거
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_progress(self, check_type: str, progress: int, message: str, status: str = "running"):
        """점검 진행 상황 전송"""
        await self.broadcast({
            "type": "progress",
            "check_type": check_type,
            "progress": progress,
            "message": message,
            "status": status
        })
    
    async def send_result(self, check_type: str, result: dict):
        """점검 결과 전송"""
        await self.broadcast({
            "type": "result",
            "check_type": check_type,
            "result": result
        })
    
    async def send_error(self, check_type: str, error: str):
        """에러 메시지 전송"""
        await self.broadcast({
            "type": "error",
            "check_type": check_type,
            "error": error
        })


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()

