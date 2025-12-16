"""
점검 모듈 레지스트리
플러그인 패턴으로 점검 모듈을 동적으로 등록 및 관리
"""
import logging
from typing import Dict, Type, Optional
from .base import BaseChecker

logger = logging.getLogger(__name__)


class CheckerRegistry:
    """점검 모듈 레지스트리 (싱글톤 패턴)"""
    
    _instance = None
    _registry: Dict[str, Type[BaseChecker]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CheckerRegistry, cls).__new__(cls)
        return cls._instance
    
    def register(self, name: str, checker_class: Type[BaseChecker]):
        """
        점검 모듈 등록
        
        Args:
            name: 점검 모듈 이름
            checker_class: BaseChecker를 상속한 클래스
        """
        if not issubclass(checker_class, BaseChecker):
            raise TypeError(f"{checker_class.__name__} must inherit from BaseChecker")
        
        self._registry[name] = checker_class
        logger.debug(f"체커 등록: {name} -> {checker_class.__name__}")
    
    def get(self, name: str) -> Optional[Type[BaseChecker]]:
        """
        점검 모듈 가져오기
        
        Args:
            name: 점검 모듈 이름
        
        Returns:
            체커 클래스 또는 None
        """
        return self._registry.get(name)
    
    def list_all(self) -> list:
        """
        등록된 모든 점검 모듈 이름 반환
        
        Returns:
            점검 모듈 이름 리스트
        """
        return list(self._registry.keys())
    
    def create(self, name: str, config: Optional[Dict] = None) -> Optional[BaseChecker]:
        """
        점검 모듈 인스턴스 생성
        
        Args:
            name: 점검 모듈 이름
            config: 설정 딕셔너리
        
        Returns:
            체커 인스턴스 또는 None
        """
        checker_class = self.get(name)
        if checker_class is None:
            logger.warning(f"등록되지 않은 체커: {name}")
            return None
        
        try:
            return checker_class(config=config)
        except Exception as e:
            logger.error(f"체커 인스턴스 생성 실패 ({name}): {e}")
            return None


# 전역 레지스트리 인스턴스
registry = CheckerRegistry()


def register_checker(name: str):
    """
    데코레이터: 점검 모듈 자동 등록
    
    Usage:
        @register_checker('ups')
        class UPSChecker(BaseChecker):
            pass
    """
    def decorator(checker_class: Type[BaseChecker]):
        registry.register(name, checker_class)
        return checker_class
    return decorator
