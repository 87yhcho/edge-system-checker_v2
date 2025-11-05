"""
타임아웃 관리 모듈
함수 실행 시 타임아웃을 적용하는 데코레이터 및 유틸리티
"""
import signal
import os
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """타임아웃 발생 예외"""
    pass


class Timeout:
    """타임아웃 데코레이터 (Windows와 Linux 모두 지원)"""
    
    def __init__(self, seconds: int):
        self.seconds = seconds
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Windows는 signal.SIGALRM을 지원하지 않으므로 다른 방식 사용
            if os.name == 'nt':
                # Windows: threading.Timer 사용
                return self._timeout_windows(func, *args, **kwargs)
            else:
                # Linux/Unix: signal.SIGALRM 사용
                return self._timeout_unix(func, *args, **kwargs)
        
        return wrapper
    
    def _timeout_unix(self, func: Callable, *args, **kwargs):
        """Unix/Linux용 타임아웃 처리"""
        def handler(signum, frame):
            raise TimeoutError(f"Function {func.__name__} timed out after {self.seconds}s")
        
        # 기존 핸들러 저장
        old_handler = signal.signal(signal.SIGALRM, handler)
        signal.alarm(self.seconds)
        
        try:
            result = func(*args, **kwargs)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        
        return result
    
    def _timeout_windows(self, func: Callable, *args, **kwargs):
        """Windows용 타임아웃 처리 (threading 사용)"""
        import threading
        
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(self.seconds)
        
        if thread.is_alive():
            logger.warning(f"Function {func.__name__} timed out after {self.seconds}s")
            raise TimeoutError(f"Function {func.__name__} timed out after {self.seconds}s")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]


def timeout(seconds: int):
    """
    타임아웃 데코레이터
    
    Usage:
        @timeout(30)
        def my_function():
            # 30초 이내에 실행되어야 함
            pass
    """
    return Timeout(seconds)


def get_timeout_config() -> dict:
    """
    환경변수에서 타임아웃 설정 읽기
    
    Returns:
        타임아웃 설정 딕셔너리
    """
    return {
        'ups_check': int(os.getenv('TIMEOUT_UPS_CHECK', '30')),
        'camera_check': int(os.getenv('TIMEOUT_CAMERA_CHECK', '120')),
        'nas_check': int(os.getenv('TIMEOUT_NAS_CHECK', '60')),
        'system_check': int(os.getenv('TIMEOUT_SYSTEM_CHECK', '90')),
        'ssh_connection': int(os.getenv('TIMEOUT_SSH_CONNECTION', '15')),
        'rtsp_connection': int(os.getenv('TIMEOUT_RTSP_CONNECTION', '10')),
    }

