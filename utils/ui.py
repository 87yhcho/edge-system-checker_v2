"""
CLI UI 유틸리티 모듈
colorama를 사용한 색상 출력, 테이블 포맷팅, 사용자 입력 처리
로깅 시스템과 통합
"""
import sys
import logging
from colorama import init, Fore, Style

# colorama 초기화 (Windows 지원)
init(autoreset=True)

# 로거 가져오기 (초기화 후 사용)
def _get_logger():
    """로거 인스턴스 가져오기"""
    return logging.getLogger(__name__)


class Colors:
    """색상 상수"""
    PASS = Fore.GREEN
    FAIL = Fore.RED
    SKIP = Fore.YELLOW
    INFO = Fore.CYAN
    WARNING = Fore.YELLOW
    HEADER = Fore.MAGENTA
    RESET = Style.RESET_ALL


def print_header(text: str):
    """헤더 출력 (로거 래퍼)"""
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.HEADER}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.RESET}\n")
    _get_logger().info(f"=== {text} ===")


def print_section(section_num: int, total: int, title: str):
    """섹션 제목 출력 (로거 래퍼)"""
    print(f"\n{Colors.INFO}[{section_num}/{total}] {title}{Colors.RESET}")
    print(f"{Colors.INFO}{'-' * 80}{Colors.RESET}")
    _get_logger().info(f"[{section_num}/{total}] {title}")


def print_pass(text: str):
    """PASS 메시지 출력 (로거 래퍼)"""
    print(f"{Colors.PASS}✓ {text}{Colors.RESET}")
    _get_logger().info(f"PASS: {text}")


def print_fail(text: str):
    """FAIL 메시지 출력 (로거 래퍼)"""
    print(f"{Colors.FAIL}✗ {text}{Colors.RESET}")
    _get_logger().error(f"FAIL: {text}")


def print_skip(text: str):
    """SKIP 메시지 출력 (로거 래퍼)"""
    print(f"{Colors.SKIP}⊘ {text}{Colors.RESET}")
    _get_logger().warning(f"SKIP: {text}")


def print_info(text: str):
    """정보 메시지 출력 (로거 래퍼)"""
    print(f"{Colors.INFO}ℹ {text}{Colors.RESET}")
    _get_logger().info(text)


def print_warning(text: str):
    """경고 메시지 출력 (로거 래퍼)"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.RESET}")
    _get_logger().warning(text)


def print_table(headers: list, rows: list):
    """간단한 테이블 출력"""
    if not rows:
        print_info("데이터가 없습니다.")
        return
    
    # 각 컬럼의 최대 너비 계산
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 헤더 출력
    header_line = " | ".join([h.ljust(col_widths[i]) for i, h in enumerate(headers)])
    print(header_line)
    print("-" * len(header_line))
    
    # 행 출력
    for row in rows:
        row_line = " | ".join([str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)])
        print(row_line)


def print_key_value(key: str, value: str, status: str = None):
    """키-값 쌍 출력 (선택적으로 상태 표시)"""
    if status == "PASS":
        print(f"  {key}: {Colors.PASS}{value}{Colors.RESET}")
    elif status == "FAIL":
        print(f"  {key}: {Colors.FAIL}{value}{Colors.RESET}")
    elif status == "SKIP":
        print(f"  {key}: {Colors.SKIP}{value}{Colors.RESET}")
    else:
        print(f"  {key}: {value}")


def ask_continue(prompt: str = "계속하시겠습니까?") -> str:
    """
    사용자에게 계속 진행 여부 확인
    Returns: 'continue', 'retry', 'quit'
    """
    print(f"\n{prompt}")
    print(f"  {Colors.INFO}[Enter] 계속  [r] 다시 점검  [q] 종료{Colors.RESET}")
    
    try:
        response = input("> ").strip().lower()
        if response == '':
            return 'continue'
        elif response == 'r':
            return 'retry'
        elif response == 'q':
            return 'quit'
        else:
            return 'continue'  # 기본값
    except (KeyboardInterrupt, EOFError):
        return 'quit'


def ask_camera_result(camera_name: str) -> str:
    """
    카메라 점검 결과 입력 받기
    Returns: 'pass', 'fail', 'skip', 'quit'
    """
    print(f"\n{camera_name} 점검 결과를 입력하세요:")
    print(f"  {Colors.PASS}[p] PASS{Colors.RESET}  {Colors.FAIL}[f] FAIL{Colors.RESET}  "
          f"{Colors.SKIP}[s] SKIP{Colors.RESET}  [q] 종료")
    
    try:
        response = input("> ").strip().lower()
        if response == 'p':
            return 'pass'
        elif response == 'f':
            return 'fail'
        elif response == 's':
            return 'skip'
        elif response == 'q':
            return 'quit'
        else:
            return 'skip'  # 기본값
    except (KeyboardInterrupt, EOFError):
        return 'quit'


def ask_input(prompt: str, default: str = None) -> str:
    """일반 입력 받기"""
    if default:
        full_prompt = f"{prompt} (기본값: {default}): "
    else:
        full_prompt = f"{prompt}: "
    
    try:
        response = input(full_prompt).strip()
        if not response and default:
            return default
        return response
    except (KeyboardInterrupt, EOFError):
        if default:
            return default
        return ""


def clear_screen():
    """화면 지우기 (선택사항)"""
    # Windows
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

