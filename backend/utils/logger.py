"""
로깅 시스템 모듈
Python logging 모듈을 사용한 체계적인 로그 관리
"""
import os
import logging
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from colorama import Fore, Style, init

# colorama 초기화
init(autoreset=True)


class ColoredConsoleHandler(logging.StreamHandler):
    """색상이 적용된 콘솔 핸들러"""
    
    COLOR_MAP = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.CYAN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }
    
    def emit(self, record):
        try:
            msg = self.format(record)
            color = self.COLOR_MAP.get(record.levelno, '')
            stream = self.stream
            stream.write(f"{color}{msg}{Style.RESET_ALL}\n")
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logger(log_dir: str = "reports/logs", level: str = "INFO") -> tuple[logging.Logger, str]:
    """
    로거 초기화
    
    Args:
        log_dir: 로그 파일 저장 디렉토리
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        (logger, log_file_path) 튜플
    """
    # 로그 디렉토리 생성
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일 경로
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"checker_{timestamp}.log")
    
    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 파일 핸들러만 추가 (콘솔에는 출력하지 않음)
    # utils.ui의 print 함수들이 콘솔 출력을 담당
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 로그 로테이션 설정 (30일 이상 된 로그 삭제)
    _cleanup_old_logs(log_dir, days=30)
    
    return logger, log_file


def _cleanup_old_logs(log_dir: str, days: int = 30):
    """
    오래된 로그 파일 삭제
    
    Args:
        log_dir: 로그 디렉토리
        days: 보관 기간 (일)
    """
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if not os.path.exists(log_dir):
            return
        
        for filename in os.listdir(log_dir):
            if filename.startswith('checker_') and filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_time < cutoff_date:
                        os.remove(filepath)
                except Exception:
                    pass  # 파일 삭제 실패 시 무시
    except Exception:
        pass  # 정리 실패 시 무시


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 가져오기
    
    Args:
        name: 모듈 이름 (보통 __name__)
    
    Returns:
        Logger 인스턴스
    """
    return logging.getLogger(name)

