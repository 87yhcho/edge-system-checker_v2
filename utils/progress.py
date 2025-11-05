"""
프로그레스 바 모듈
텍스트 기반 진행 상황 표시
"""
import sys
import time
from typing import Optional


class ProgressBar:
    """텍스트 기반 프로그레스 바"""
    
    def __init__(self, total: int, desc: str = "Progress", width: int = 50):
        """
        프로그레스 바 초기화
        
        Args:
            total: 전체 단계 수
            desc: 설명 텍스트
            width: 프로그레스 바 너비 (문자 수)
        """
        self.total = total
        self.current = 0
        self.desc = desc
        self.width = width
        self.start_time = time.time()
        self.last_update_time = time.time()
    
    def update(self, step: int = 1, status: Optional[str] = None):
        """
        진행 상황 업데이트
        
        Args:
            step: 진행할 단계 수
            status: 추가 상태 메시지
        """
        self.current = min(self.current + step, self.total)
        self._render(status)
    
    def set(self, value: int, status: Optional[str] = None):
        """
        현재 값을 직접 설정
        
        Args:
            value: 설정할 값
            status: 추가 상태 메시지
        """
        self.current = min(max(value, 0), self.total)
        self._render(status)
    
    def _render(self, status: Optional[str] = None):
        """프로그레스 바 렌더링"""
        if self.total == 0:
            return
        
        percent = int(self.current / self.total * 100)
        filled = int(self.width * self.current / self.total)
        bar = '=' * filled + '>' + ' ' * (self.width - filled - 1)
        
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current * (self.total - self.current)) if self.current < self.total else 0
            rate = self.current / elapsed if elapsed > 0 else 0
        else:
            eta = 0
            rate = 0
        
        # 상태 메시지 포함
        status_text = f" | {status}" if status else ""
        
        # 출력 포맷
        line = f'\r{self.desc}: [{bar}] {percent}% ({self.current}/{self.total}) | '
        line += f'Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s | Rate: {rate:.2f}/s{status_text}'
        
        sys.stdout.write(line)
        sys.stdout.flush()
        self.last_update_time = time.time()
    
    def finish(self, message: Optional[str] = None):
        """
        프로그레스 바 완료
        
        Args:
            message: 완료 메시지
        """
        self.current = self.total
        self._render()
        sys.stdout.write('\n')
        sys.stdout.flush()
        
        if message:
            elapsed = time.time() - self.start_time
            print(f"{message} (완료 시간: {elapsed:.1f}초)")
    
    def reset(self):
        """프로그레스 바 리셋"""
        self.current = 0
        self.start_time = time.time()
        self.last_update_time = time.time()


class SimpleProgress:
    """간단한 프로그레스 표시 (단계별)"""
    
    def __init__(self, total: int, desc: str = "진행 중"):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = time.time()
    
    def next(self, message: Optional[str] = None):
        """다음 단계로 이동"""
        self.current += 1
        elapsed = time.time() - self.start_time
        status = f"[{self.current}/{self.total}]"
        
        if message:
            print(f"{status} {message} (경과: {elapsed:.1f}초)")
        else:
            print(f"{status} {self.desc} (경과: {elapsed:.1f}초)")
    
    def finish(self, message: Optional[str] = None):
        """완료"""
        elapsed = time.time() - self.start_time
        if message:
            print(f"완료: {message} (총 시간: {elapsed:.1f}초)")
        else:
            print(f"완료 (총 시간: {elapsed:.1f}초)")

