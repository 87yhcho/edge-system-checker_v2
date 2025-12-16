"""
애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 앱 기본 설정
    APP_NAME: str = "Edge System Checker Web"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite+aiosqlite:///./check_history.db"
    
    # CORS 설정
    CORS_ORIGINS: list[str] = ["*"]
    
    # PostgreSQL 설정 (기존)
    PG_HOST: str = "localhost"
    PG_PORT: int = 5432
    PG_DB: str = "blackbox"
    PG_USER: str = "postgres"
    PG_PASS: str = ""
    
    # NUT/UPS 설정
    NUT_UPS_NAME: str = "ups"
    
    # NAS 설정
    NAS_IP: str = "192.168.10.30"
    NAS_USER: str = "admin2k"
    NAS_PASSWORD: str = ""
    NAS_PORT: int = 2222
    
    # 카메라 설정
    CAMERA_BASE_IP: str = "192.168.1"
    CAMERA_START_IP: str = "101"
    CAMERA_USER: str = "root"
    CAMERA_PASS: str = "root"
    CAMERA_RTSP_PATH: str = "cam0_0"
    CAMERA_RTSP_PORT: int = 554
    CAMERA_MEDIAMTX_BASE_PORT: int = 1111
    CAMERA_LOG_BASE_PATH: str = "/mnt/nas/logs"
    CAMERA_VIDEO_BASE_PATH: str = "/mnt/nas/cam"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 30
    
    # 타임아웃 설정 (초)
    TIMEOUT_UPS_CHECK: int = 30
    TIMEOUT_CAMERA_CHECK: int = 120
    TIMEOUT_NAS_CHECK: int = 60
    TIMEOUT_SYSTEM_CHECK: int = 90
    TIMEOUT_SSH_CONNECTION: int = 15
    TIMEOUT_RTSP_CONNECTION: int = 10
    
    # 스케줄러 설정
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_CRON_HOUR: int = 1  # 매일 새벽 1시
    SCHEDULER_CRON_MINUTE: int = 0
    
    # 알림 설정
    NOTIFICATION_ENABLED: bool = False
    NOTIFICATION_EMAIL_ENABLED: bool = False
    NOTIFICATION_SLACK_ENABLED: bool = False
    
    # 이메일 설정
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TO: Optional[str] = None
    
    # 슬랙 설정
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()

