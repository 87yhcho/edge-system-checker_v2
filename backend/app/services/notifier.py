"""
알림 서비스
이메일 및 슬랙 알림 발송
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
import logging
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotifierService:
    """알림 서비스 클래스"""
    
    async def send_check_failure_notification(self, result: Dict[str, Any]):
        """
        점검 실패 알림 발송
        
        Args:
            result: 점검 결과
        """
        if not settings.NOTIFICATION_ENABLED:
            return
        
        # 이메일 알림
        if settings.NOTIFICATION_EMAIL_ENABLED:
            await self._send_email_notification(result)
        
        # 슬랙 알림
        if settings.NOTIFICATION_SLACK_ENABLED:
            await self._send_slack_notification(result)
    
    async def _send_email_notification(self, result: Dict[str, Any]):
        """이메일 알림 발송"""
        if not all([
            settings.SMTP_HOST,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM,
            settings.SMTP_TO
        ]):
            logger.warning("이메일 설정이 완료되지 않았습니다.")
            return
        
        try:
            # 메일 내용 생성
            subject = f"[Edge System Checker] 점검 실패 알림"
            
            # 실패한 점검 항목 추출
            failed_checks = []
            summary = result.get('summary', {})
            for check_type, status in summary.items():
                if status in ['FAIL', 'ERROR']:
                    failed_checks.append(f"- {check_type}: {status}")
            
            body = f"""
점검 실패 알림

점검 시간: {result.get('timestamp', 'N/A')}
소요 시간: {result.get('duration_seconds', 0)}초

실패한 점검 항목:
{chr(10).join(failed_checks) if failed_checks else '없음'}

상세 결과는 웹 대시보드에서 확인하실 수 있습니다.
"""
            
            # 이메일 메시지 생성
            message = MIMEMultipart()
            message["From"] = settings.SMTP_FROM
            message["To"] = settings.SMTP_TO
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain", "utf-8"))
            
            # SMTP 서버로 전송
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True
            )
            
            logger.info("이메일 알림 발송 완료")
        
        except Exception as e:
            logger.error(f"이메일 알림 발송 실패: {e}", exc_info=True)
    
    async def _send_slack_notification(self, result: Dict[str, Any]):
        """슬랙 알림 발송"""
        if not settings.SLACK_WEBHOOK_URL:
            logger.warning("슬랙 웹훅 URL이 설정되지 않았습니다.")
            return
        
        try:
            # 실패한 점검 항목 추출
            failed_checks = []
            summary = result.get('summary', {})
            for check_type, status in summary.items():
                if status in ['FAIL', 'ERROR']:
                    failed_checks.append(f"• {check_type}: {status}")
            
            # 슬랙 메시지 생성
            text = f"*[Edge System Checker] 점검 실패 알림*\n\n"
            text += f"점검 시간: {result.get('timestamp', 'N/A')}\n"
            text += f"소요 시간: {result.get('duration_seconds', 0)}초\n\n"
            text += f"*실패한 점검 항목:*\n"
            text += "\n".join(failed_checks) if failed_checks else "없음"
            
            payload = {
                "text": text,
                "username": "Edge System Checker",
                "icon_emoji": ":warning:"
            }
            
            # 슬랙 웹훅으로 전송
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
            
            logger.info("슬랙 알림 발송 완료")
        
        except Exception as e:
            logger.error(f"슬랙 알림 발송 실패: {e}", exc_info=True)


# 전역 인스턴스
notifier = NotifierService()

