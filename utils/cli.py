"""
CLI 인자 파싱 모듈
명령행 인자 처리 및 검증
"""
import argparse
import sys
from typing import List, Optional


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    CLI 인자 파싱
    
    Args:
        args: 파싱할 인자 리스트 (None이면 sys.argv 사용)
    
    Returns:
        파싱된 인자 네임스페이스
    """
    parser = argparse.ArgumentParser(
        description='Edge 시스템 점검 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 모든 항목 점검 (대화형 모드)
  python checker.py
  
  # 특정 항목만 점검 (자동 모드)
  python checker.py --checks ups nas --auto
  
  # 카메라만 점검 (4대)
  python checker.py --checks camera --camera-count 4 --auto
  
  # 특정 항목만 점검 (수동 모드)
  python checker.py --checks system --interactive
        """
    )
    
    # 점검 항목 선택
    parser.add_argument(
        '--checks',
        nargs='+',
        choices=['ups', 'camera', 'nas', 'system', 'all'],
        default=['all'],
        help='점검할 항목 선택 (기본값: all)'
    )
    
    # 실행 모드
    parser.add_argument(
        '--auto',
        action='store_true',
        help='자동 모드 (확인 없이 자동 진행)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='수동 모드 (각 항목마다 확인)'
    )
    
    # 카메라 설정
    parser.add_argument(
        '--camera-count',
        type=int,
        default=None,
        help='점검할 카메라 개수 (기본값: 대화형 입력)'
    )
    
    parser.add_argument(
        '--camera-mode',
        choices=['gui', 'auto'],
        default=None,
        help='카메라 점검 모드 (gui: 영상 확인, auto: 자동 검증)'
    )
    
    # 리포트 설정
    parser.add_argument(
        '--output-format',
        nargs='+',
        choices=['txt', 'json', 'html'],
        default=['txt', 'json', 'html'],
        help='리포트 출력 포맷 (기본값: txt, json, html 모두)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='리포트 저장 디렉토리 (기본값: 현재 디렉토리)'
    )
    
    # 로깅 설정
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=None,
        help='로그 레벨 (기본값: 환경변수 또는 INFO)'
    )
    
    # 리스트 모드
    parser.add_argument(
        '--list-checks',
        action='store_true',
        help='등록된 점검 항목 목록 출력 후 종료'
    )
    
    # 버전 정보
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    parsed_args = parser.parse_args(args)
    
    # 'all' 처리
    if 'all' in parsed_args.checks:
        parsed_args.checks = ['ups', 'camera', 'nas', 'system']
    
    # 실행 모드 기본값 (둘 다 지정 안 하면 대화형)
    if not parsed_args.auto and not parsed_args.interactive:
        parsed_args.interactive = True  # 기본값은 수동 모드
    
    return parsed_args


def validate_args(args: argparse.Namespace) -> bool:
    """
    인자 검증
    
    Args:
        args: 파싱된 인자 네임스페이스
    
    Returns:
        검증 성공 여부
    """
    # 카메라 설정 검증
    if 'camera' in args.checks:
        if args.camera_count is not None and args.camera_count < 0:
            print("오류: 카메라 개수는 0 이상이어야 합니다.", file=sys.stderr)
            return False
    
    # 출력 디렉토리 검증
    import os
    if args.output_dir and not os.path.isdir(args.output_dir):
        print(f"오류: 출력 디렉토리가 존재하지 않습니다: {args.output_dir}", file=sys.stderr)
        return False
    
    return True
