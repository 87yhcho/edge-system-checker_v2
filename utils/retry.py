"""
재시도 메커니즘 모듈
지수 백오프를 사용한 재시도 데코레이터
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    지수 백오프 재시도 데코레이터
    
    Args:
        max_retries: 최대 재시도 횟수
        base_delay: 초기 지연 시간 (초)
        backoff_factor: 지수 백오프 계수
        exceptions: 재시도할 예외 타입
    
    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1, backoff_factor=2)
        def my_function():
            # 재시도 로직이 적용됨
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise
                    
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"{func.__name__} attempt {attempt+1}/{max_retries} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            
            # 이 코드는 실행되지 않아야 함 (위에서 예외 발생)
            raise RuntimeError(f"{func.__name__} failed after {max_retries} attempts")
        
        return wrapper
    return decorator

