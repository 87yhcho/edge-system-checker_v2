"""
커스텀 예외 클래스
체계적인 예외 처리
"""


class CheckerError(Exception):
    """체커 기본 예외"""
    pass


class ConnectionError(CheckerError):
    """연결 실패 예외 (SSH, RTSP, NUT 등)"""
    pass


class TimeoutError(CheckerError):
    """타임아웃 예외"""
    pass


class ConfigurationError(CheckerError):
    """설정 오류 예외"""
    pass


class ValidationError(CheckerError):
    """검증 실패 예외"""
    pass

