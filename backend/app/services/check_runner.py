"""
점검 실행 서비스
기존 체크 모듈을 호출하고 WebSocket으로 진행 상황을 전송
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

from app.core.config import settings
from app.core.websocket import manager
from app.models.check_history import CheckHistory
from sqlalchemy.ext.asyncio import AsyncSession

# 기존 체크 모듈 import
import sys
import os
# backend/app/services에서 backend/checks까지의 경로
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
checks_dir = os.path.join(backend_dir, "checks")
if checks_dir not in sys.path:
    sys.path.insert(0, checks_dir)

from checks.ups_check import check_ups_status
from checks.camera_check import check_cameras
from checks.nas_check import check_nas_status
from checks.system_check import check_system_status

logger = logging.getLogger(__name__)


class CheckRunner:
    """점검 실행 클래스"""
    
    def __init__(self):
        self.current_check: Optional[str] = None
        self.is_running: bool = False
    
    async def run_all_checks(
        self,
        db: AsyncSession,
        selected_checks: List[str] = None,
        camera_count: int = 4,
        auto_mode: bool = True
    ) -> Dict[str, Any]:
        """
        모든 점검 실행
        
        Args:
            db: 데이터베이스 세션
            selected_checks: 실행할 점검 목록 (None이면 모두 실행)
            camera_count: 카메라 개수
            auto_mode: 카메라 점검 자동 모드
        
        Returns:
            점검 결과 딕셔너리
        """
        if self.is_running:
            raise Exception("점검이 이미 실행 중입니다.")
        
        self.is_running = True
        start_time = time.time()
        
        if selected_checks is None:
            selected_checks = ['ups', 'camera', 'nas', 'system']
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'checks': {}
        }
        
        try:
            # 각 점검 실행
            total_checks = len(selected_checks)
            for idx, check_type in enumerate(selected_checks):
                self.current_check = check_type
                progress = int((idx / total_checks) * 100)
                
                await manager.send_progress(
                    check_type="all",
                    progress=progress,
                    message=f"{check_type.upper()} 점검 시작...",
                    status="running"
                )
                
                try:
                    if check_type == 'ups':
                        result = await self._run_ups_check()
                    elif check_type == 'camera':
                        result = await self._run_camera_check(camera_count, auto_mode)
                    elif check_type == 'nas':
                        result = await self._run_nas_check()
                    elif check_type == 'system':
                        result = await self._run_system_check()
                    else:
                        result = {'status': 'SKIP', 'reason': f'Unknown check type: {check_type}'}
                    
                    results['checks'][check_type] = result
                    results['summary'][check_type] = result.get('status', 'UNKNOWN')
                    
                    # 결과를 WebSocket으로 전송
                    await manager.send_result(check_type=check_type, result=result)
                    
                    # 개별 점검 완료 진행 상황 전송
                    completed_progress = int(((idx + 1) / total_checks) * 100)
                    await manager.send_progress(
                        check_type="all",
                        progress=completed_progress,
                        message=f"{check_type.upper()} 점검 완료 - {result.get('status', 'UNKNOWN')}",
                        status="running"
                    )
                    
                    # DB에 저장
                    await self._save_to_db(db, check_type, result, time.time() - start_time, camera_count)
                    
                except Exception as e:
                    logger.error(f"{check_type} 점검 중 오류: {e}", exc_info=True)
                    error_result = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    results['checks'][check_type] = error_result
                    results['summary'][check_type] = 'ERROR'
                    
                    await manager.send_error(check_type=check_type, error=str(e))
                    await self._save_to_db(db, check_type, error_result, time.time() - start_time, camera_count)
            
            # 전체 요약 생성
            overall_status = 'PASS'
            for check_type, status in results['summary'].items():
                if status in ['FAIL', 'ERROR']:
                    overall_status = 'FAIL'
                    break
                elif status == 'SKIP' and overall_status == 'PASS':
                    overall_status = 'SKIP'
            
            results['summary']['overall'] = overall_status
            results['duration_seconds'] = int(time.time() - start_time)
            
            # 전체 결과를 DB에 저장
            await self._save_to_db(db, 'all', results, time.time() - start_time, camera_count)
            
            # 완료 메시지 전송
            await manager.send_progress(
                check_type="all",
                progress=100,
                message="모든 점검 완료",
                status="completed"
            )
            
            await manager.send_result(check_type="all", result=results)
            
        finally:
            self.is_running = False
            self.current_check = None
        
        return results
    
    async def _run_ups_check(self) -> Dict[str, Any]:
        """UPS 점검 실행"""
        await manager.send_progress("ups", 0, "UPS/NUT 서비스 확인 중...")
        
        # 동기 함수를 비동기로 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            check_ups_status,
            settings.NUT_UPS_NAME,
            settings.NAS_IP
        )
        
        await manager.send_progress("ups", 100, f"UPS 점검 완료: {result.get('status', 'UNKNOWN')}")
        return result
    
    async def _run_camera_check(self, camera_count: int, auto_mode: bool) -> Dict[str, Any]:
        """카메라 점검 실행"""
        await manager.send_progress("camera", 0, f"카메라 {camera_count}대 점검 시작...")
        
        camera_config = {
            'base_ip': settings.CAMERA_BASE_IP,
            'start_ip': settings.CAMERA_START_IP,
            'username': settings.CAMERA_USER,
            'password': settings.CAMERA_PASS,
            'rtsp_path': settings.CAMERA_RTSP_PATH,
            'rtsp_port': str(settings.CAMERA_RTSP_PORT),
            'mediamtx_base_port': str(settings.CAMERA_MEDIAMTX_BASE_PORT),
            'log_base_path': settings.CAMERA_LOG_BASE_PATH,
            'video_base_path': settings.CAMERA_VIDEO_BASE_PATH
        }
        
        # 동기 함수를 비동기로 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            check_cameras,
            camera_count,
            camera_config,
            auto_mode
        )
        
        await manager.send_progress("camera", 100, f"카메라 점검 완료: {result.get('status', 'UNKNOWN')}")
        return result
    
    async def _run_nas_check(self) -> Dict[str, Any]:
        """NAS 점검 실행"""
        await manager.send_progress("nas", 0, "NAS 연결 확인 중...")
        
        nas_config = {
            'ip': settings.NAS_IP,
            'user': settings.NAS_USER,
            'password': settings.NAS_PASSWORD,
            'port': str(settings.NAS_PORT)
        }
        
        # 동기 함수를 비동기로 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            check_nas_status,
            nas_config
        )
        
        await manager.send_progress("nas", 100, f"NAS 점검 완료: {result.get('status', 'UNKNOWN')}")
        return result
    
    async def _run_system_check(self) -> Dict[str, Any]:
        """시스템 점검 실행"""
        await manager.send_progress("system", 0, "시스템 점검 시작...")
        
        # 동기 함수를 비동기로 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, check_system_status)
        
        await manager.send_progress("system", 100, f"시스템 점검 완료: {result.get('status', 'UNKNOWN')}")
        return result
    
    async def _save_to_db(
        self,
        db: AsyncSession,
        check_type: str,
        result: Dict[str, Any],
        duration: float,
        camera_count: Optional[int] = None
    ):
        """점검 결과를 DB에 저장"""
        try:
            # datetime 객체를 문자열로 변환하는 재귀 함수
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: serialize_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_datetime(item) for item in obj]
                return obj
            
            # 결과를 JSON 직렬화 가능하게 변환
            serialized_result = serialize_datetime(result)
            
            status = serialized_result.get('status', 'UNKNOWN')
            error_message = serialized_result.get('error') if status == 'ERROR' else None
            
            history = CheckHistory(
                check_type=check_type,
                status=status,
                results=serialized_result,
                error_message=error_message,
                duration_seconds=int(duration),
                camera_count=camera_count if check_type == 'camera' else None
            )
            
            db.add(history)
            await db.commit()
            await db.refresh(history)
            
            logger.info(f"점검 결과 저장 완료: {check_type} - {status}")
        except Exception as e:
            logger.error(f"점검 결과 저장 실패: {e}", exc_info=True)
            await db.rollback()


# 전역 인스턴스
check_runner = CheckRunner()

