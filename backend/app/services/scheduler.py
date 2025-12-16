"""
스케줄러 서비스
APScheduler를 사용하여 주기적 점검 실행
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.core.config import settings
from app.services.check_runner import check_runner
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class SchedulerService:
    """스케줄러 서비스 클래스"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_started = False
    
    def start(self):
        """스케줄러 시작"""
        if self.is_started:
            logger.warning("스케줄러가 이미 시작되었습니다.")
            return
        
        if not settings.SCHEDULER_ENABLED:
            logger.info("스케줄러가 비활성화되어 있습니다.")
            return
        
        # 주기적 점검 작업 등록
        self.scheduler.add_job(
            self._run_scheduled_check,
            trigger=CronTrigger(
                hour=settings.SCHEDULER_CRON_HOUR,
                minute=settings.SCHEDULER_CRON_MINUTE
            ),
            id="daily_check",
            name="일일 자동 점검",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_started = True
        logger.info(f"스케줄러 시작됨: 매일 {settings.SCHEDULER_CRON_HOUR:02d}:{settings.SCHEDULER_CRON_MINUTE:02d}에 실행")
    
    def shutdown(self):
        """스케줄러 종료"""
        if not self.is_started:
            return
        
        self.scheduler.shutdown()
        self.is_started = False
        logger.info("스케줄러 종료됨")
    
    async def _run_scheduled_check(self):
        """스케줄된 점검 실행"""
        logger.info("스케줄된 점검 시작")
        
        try:
            # 데이터베이스 세션 생성
            async with AsyncSessionLocal() as db:
                # 모든 점검 실행
                result = await check_runner.run_all_checks(
                    db=db,
                    selected_checks=None,  # 모든 점검 실행
                    camera_count=4,  # 기본값, 설정에서 가져올 수 있음
                    auto_mode=True
                )
                
                logger.info(f"스케줄된 점검 완료: {result.get('summary', {}).get('overall', 'UNKNOWN')}")
                
                # 알림 서비스 호출 (실패 시)
                if result.get('summary', {}).get('overall') == 'FAIL':
                    from app.services.notifier import notifier
                    await notifier.send_check_failure_notification(result)
        
        except Exception as e:
            logger.error(f"스케줄된 점검 실행 중 오류: {e}", exc_info=True)


# 전역 인스턴스
scheduler_service = SchedulerService()

