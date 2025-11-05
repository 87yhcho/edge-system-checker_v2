"""
점검 모듈 베이스 클래스
모든 점검 모듈이 상속받는 공통 인터페이스
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseChecker(ABC):
    """점검 모듈 베이스 클래스"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        초기화
        
        Args:
            config: 점검 설정 딕셔너리
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abstractmethod
    def check(self) -> Dict[str, Any]:
        """
        점검 실행 (서브클래스에서 구현)
        
        Returns:
            점검 결과 딕셔너리
        """
        pass
    
    def run(self) -> Dict[str, Any]:
        """
        점검 실행 래퍼 (예외 처리 포함)
        
        Returns:
            점검 결과 딕셔너리 (항상 'status' 키 포함)
        """
        try:
            self.logger.info(f"{self.name} 점검 시작")
            result = self.check()
            
            # result에 status가 없으면 추가
            if 'status' not in result:
                result['status'] = 'PASS' if not result.get('errors') else 'FAIL'
            
            result['checker_name'] = self.name
            result['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.logger.info(f"{self.name} 점검 완료: {result.get('status', 'UNKNOWN')}")
            return result
            
        except Exception as e:
            self.logger.error(f"{self.name} 점검 중 오류 발생: {e}", exc_info=True)
            return {
                'status': 'ERROR',
                'checker_name': self.name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def validate_config(self, required_keys: list) -> bool:
        """
        설정 검증
        
        Args:
            required_keys: 필수 설정 키 리스트
        
        Returns:
            검증 성공 여부
        """
        missing = [key for key in required_keys if key not in self.config]
        if missing:
            self.logger.warning(f"필수 설정 누락: {missing}")
            return False
        return True
    
    def get_status_icon(self, status: str) -> str:
        """
        상태에 따른 아이콘 반환
        
        Args:
            status: 상태 (PASS, FAIL, WARN, SKIP, ERROR)
        
        Returns:
            아이콘 문자열
        """
        icons = {
            'PASS': '✓',
            'FAIL': '✗',
            'WARN': '⚠',
            'SKIP': '⊘',
            'ERROR': '✗'
        }
        return icons.get(status.upper(), '?')
