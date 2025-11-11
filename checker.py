#!/usr/bin/env python3
"""
Edge 시스템 점검 CLI 도구
UPS, 카메라, PostgreSQL, NAS를 순차적으로 점검하는 대화형 스크립트
"""
import os
import sys
import unicodedata
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로거 초기화 (환경변수 로드 후)
from utils.logger import setup_logger
log_level = os.getenv('LOG_LEVEL', 'INFO')
logger, log_file = setup_logger(level=log_level)

from utils.ui import (
    print_header, print_info, print_warning, print_pass, print_fail,
    ask_input, ask_continue
)
from utils.reporter import save_report, save_json_report, save_html_report, print_summary
from utils.progress import ProgressBar
from utils.cli import parse_args, validate_args

from checks.ups_check import check_ups_status
from checks.camera_check import check_cameras
from checks.pg_check import check_postgresql
from checks.nas_check import check_nas_status
from checks.system_check import check_system_status
from checks.registry import registry


def get_display_width(text):
    """
    문자열의 실제 터미널 표시 너비를 계산
    한글/중국어/일본어 등 전각 문자는 2칸, 영문/숫자 등은 1칸
    ANSI 색상 코드는 너비에서 제외
    """
    import re
    # ANSI 색상 코드 제거
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    text_without_ansi = ansi_escape.sub('', text)
    
    width = 0
    for char in text_without_ansi:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2  # 전각 문자 (한글, 중국어, 일본어 등)
        else:
            width += 1  # 반각 문자 (영문, 숫자, 기호 등)
    return width


def pad_string(text, target_width):
    """
    문자열을 목표 너비에 맞춰 오른쪽에 공백 추가
    한글 문자 너비를 고려하여 정확한 정렬
    """
    current_width = get_display_width(text)
    padding = target_width - current_width
    if padding > 0:
        return text + ' ' * padding
    return text


def get_env_config():
    """환경변수에서 설정 읽기"""
    return {
        'pg': {
            'host': os.getenv('PG_HOST', 'localhost'),
            'port': os.getenv('PG_PORT', '5432'),
            'db': os.getenv('PG_DB', 'postgres'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASS', '')
        },
        'nut': {
            'ups_name': os.getenv('NUT_UPS_NAME', 'ups')
        },
        'nas': {
            'ip': os.getenv('NAS_IP', '192.168.10.30'),
            'user': os.getenv('NAS_USER', 'admin'),
            'password': os.getenv('NAS_PASSWORD', ''),
            'port': os.getenv('NAS_PORT', '2222')  # 시놀로지 커스텀 SSH 포트 (실패 시 22로 재시도)
        },
        'camera': {
            'base_ip': os.getenv('CAMERA_BASE_IP', '192.168.1'),
            'start_ip': os.getenv('CAMERA_START_IP', '101'),
            'username': os.getenv('CAMERA_USER', 'root'),
            'password': os.getenv('CAMERA_PASS', 'root'),
            'rtsp_path': os.getenv('CAMERA_RTSP_PATH', 'cam0_0'),
            'rtsp_port': os.getenv('CAMERA_RTSP_PORT', '554'),
            'mediamtx_base_port': os.getenv('CAMERA_MEDIAMTX_BASE_PORT', '1111'),
            'log_base_path': os.getenv('CAMERA_LOG_BASE_PATH', '/mnt/nas/logs'),
            'video_base_path': os.getenv('CAMERA_VIDEO_BASE_PATH', '/mnt/nas/cam')
        }
    }


def main(args=None):
    """메인 실행 함수"""
    # CLI 인자 파싱
    cli_args = parse_args(args)
    
    # --list-checks 옵션 처리
    if cli_args.list_checks:
        print("등록된 점검 항목:")
        for check_name in ['ups', 'camera', 'nas', 'system']:
            print(f"  - {check_name}")
        sys.exit(0)
    
    # 인자 검증
    if not validate_args(cli_args):
        sys.exit(1)
    
    # 로그 레벨 설정 (CLI 인자가 우선)
    if cli_args.log_level:
        import logging
        logging.getLogger().setLevel(getattr(logging, cli_args.log_level))
        logger.setLevel(getattr(logging, cli_args.log_level))
    
    logger.info("=" * 80)
    logger.info("Edge 시스템 점검 도구 시작")
    logger.info(f"로그 파일: {log_file}")
    
    print_header("Edge 시스템 점검 도구")
    
    print_info("이 도구는 Edge 시스템의 상태를 순차적으로 점검합니다.")
    print_info(f"로그 파일: {log_file}")
    print("")
    
    # 설정 로드
    config = get_env_config()
    
    # 전체 결과 저장
    results = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'summary': {}
    }
    
    # CLI 인자에서 설정 가져오기
    selected_checks = cli_args.checks
    full_auto_mode = cli_args.auto
    
    # CLI 인자가 없으면 대화형 입력
    if not cli_args.auto and cli_args.interactive:
    # 전체 실행 모드 선택 (자동/수동)
    print_info("실행 모드를 선택하세요:")
    print("  1. 자동 모드 (모든 점검을 자동으로 진행, 확인 없이)")
    print("  2. 수동 모드 (각 항목마다 확인 후 진행)")
    run_mode_str = ask_input("실행 모드 선택 [1: 자동 / 2: 수동]", "1")
    
    if run_mode_str == "1":
        full_auto_mode = True
        print_info("🤖 자동 모드 선택: 모든 점검을 자동으로 진행합니다.")
    else:
        full_auto_mode = False
        print_info("👤 수동 모드 선택: 각 항목마다 확인 후 진행합니다.")
    print("")
        
        # 점검 항목 선택 (CLI에서 지정 안 했을 때만)
        if not cli_args.checks or cli_args.checks == ['all']:
            print_info("점검할 항목을 선택하세요:")
            print("  1. UPS/NUT 상태")
            print("  2. 카메라 RTSP")
            print("  3. NAS 상태")
            print("  4. 시스템 종합")
            check_choice = ask_input("선택 [1,2,3,4 또는 all] (쉼표로 구분)", "all")
            
            if check_choice.lower() == 'all':
                selected_checks = ['ups', 'camera', 'nas', 'system']
                print_info("✓ 모든 항목 점검")
            else:
                mapping = {'1': 'ups', '2': 'camera', '3': 'nas', '4': 'system'}
                selected_checks = []
                for num in check_choice.split(','):
                    num = num.strip()
                    if num in mapping:
                        selected_checks.append(mapping[num])
                
                if not selected_checks:
                    print_warning("선택된 항목이 없습니다. 모든 항목을 점검합니다.")
                    selected_checks = ['ups', 'camera', 'nas', 'system']
                else:
                    check_names = {'ups': 'UPS/NUT', 'camera': '카메라', 'nas': 'NAS', 'system': '시스템'}
                    selected_names = [check_names.get(c, c) for c in selected_checks]
                    print_info(f"✓ 선택된 항목: {', '.join(selected_names)}")
            print("")
    else:
        # CLI 인자 사용
        check_names = {'ups': 'UPS/NUT', 'camera': '카메라', 'nas': 'NAS', 'system': '시스템'}
        selected_names = [check_names.get(c, c) for c in selected_checks]
        print_info(f"✓ 선택된 항목: {', '.join(selected_names)}")
        if full_auto_mode:
            print_info("🤖 자동 모드로 실행합니다.")
        else:
            print_info("👤 수동 모드로 실행합니다.")
        print("")
    
    # 카메라 점검 모드 선택
    if cli_args.camera_mode:
        auto_mode = (cli_args.camera_mode == 'auto')
    else:
    print_info("카메라 점검 모드를 선택하세요:")
    print("  1. GUI 모드 (장비에서 직접 실행, 영상 확인)")
    print("  2. Auto 모드 (SSH 원격 실행, 자동 검증)")
    mode_str = ask_input("모드 선택 [1: GUI / 2: Auto]", "2")
    
        auto_mode = (mode_str != "1")
    
    if auto_mode:
        print_info("📡 Auto 모드: 영상 표시 없이 스트림 상태만 자동 검증합니다.")
    else:
        print_info("🖥️  GUI 모드: 각 카메라 영상을 확인하고 판정합니다.")
    print("")
    
    # 카메라 개수 설정
    if cli_args.camera_count is not None:
        camera_count = cli_args.camera_count
    else:
    camera_count_str = ask_input("점검할 카메라 개수를 입력하세요", "4")
    try:
        camera_count = int(camera_count_str)
        if camera_count < 0:
            camera_count = 0
    except ValueError:
        print_warning("잘못된 입력입니다. 기본값 4를 사용합니다.")
        camera_count = 4
    
    print("")
    print_info(f"점검 시작: {results['timestamp']}")
    print_info(f"카메라 개수: {camera_count}대")
    print("")
    
    # 전체 진행률 프로그레스 바 초기화
    total_checks = len(selected_checks)
    progress = ProgressBar(total=total_checks, desc="전체 점검 진행률")
    progress.update(0, "시작")
    
    # ========== 1. UPS/NUT 점검 ==========
    if 'ups' in selected_checks:
    while True:
        try:
            ups_result = check_ups_status(
                ups_name=config['nut']['ups_name'],
                nas_ip=config['nas']['ip']
            )
            results['ups'] = ups_result
                progress.update(1, "UPS 점검 완료")
            
            # 자동 모드면 확인 없이 계속 진행
            if full_auto_mode:
                print_info("자동 모드: 다음 단계로 진행합니다.")
                break
            
            # 사용자 컨펌
            user_action = ask_continue("UPS 점검 완료. 다음 단계로 진행하시겠습니까?")
            if user_action == 'quit':
                print_warning("사용자가 점검을 중단했습니다.")
                results['summary']['status'] = 'QUIT'
                    save_and_exit(results, output_formats=cli_args.output_format, output_dir=cli_args.output_dir)
                return
            elif user_action == 'retry':
                print_info("UPS 점검을 다시 수행합니다...")
                continue  # 루프 계속 (재시도)
            else:
                break  # 루프 탈출 (계속 진행)
        
        except KeyboardInterrupt:
            print("")
            print_warning("사용자가 점검을 중단했습니다.")
            results['summary']['status'] = 'INTERRUPTED'
                save_and_exit(results, output_formats=cli_args.output_format, output_dir=cli_args.output_dir)
            return
        except Exception as e:
            print_fail(f"UPS 점검 중 오류 발생: {str(e)}")
            results['ups'] = {'status': 'ERROR', 'error': str(e)}
            
            # 자동 모드면 오류 발생해도 계속 진행
            if full_auto_mode:
                print_info("자동 모드: 오류가 발생했지만 계속 진행합니다.")
                break
            
            user_action = ask_continue("오류가 발생했습니다. 계속 진행하시겠습니까?")
            if user_action == 'quit':
                    save_and_exit(results, output_formats=cli_args.output_format, output_dir=cli_args.output_dir)
                return
            elif user_action == 'retry':
                print_info("UPS 점검을 다시 수행합니다...")
                continue  # 루프 계속 (재시도)
            else:
                break  # 루프 탈출 (계속 진행)
    else:
        print_info("UPS 점검을 건너뜁니다 (선택되지 않음)")
        results['ups'] = {'status': 'SKIP', 'reason': 'Not selected'}
    
    # ========== 2. 카메라 점검 ==========
    if 'camera' in selected_checks:
        if camera_count > 0:
            while True:
                try:
                    camera_result = check_cameras(camera_count, config['camera'], auto_mode=auto_mode)
                    results['cameras'] = camera_result
                    progress.update(1, "카메라 점검 완료")
                    
                    if camera_result.get('status') == 'QUIT':
                        print_warning("사용자가 카메라 점검을 중단했습니다.")
                        results['summary']['status'] = 'QUIT'
                        save_and_exit(results)
                        return
                    
                    # 자동 모드면 확인 없이 계속 진행
                    if full_auto_mode:
                        print_info("자동 모드: 다음 단계로 진행합니다.")
                        break
                    
                    # 사용자 컨펌
                    user_action = ask_continue("카메라 점검 완료. 다음 단계로 진행하시겠습니까?")
                    if user_action == 'quit':
                        print_warning("사용자가 점검을 중단했습니다.")
                        results['summary']['status'] = 'QUIT'
                        save_and_exit(results)
                        return
                    elif user_action == 'retry':
                        print_info("카메라 점검을 다시 수행합니다...")
                        continue  # 루프 계속 (재시도)
                    else:
                        break  # 루프 탈출 (계속 진행)
            
                except KeyboardInterrupt:
                    print("")
                    print_warning("사용자가 점검을 중단했습니다.")
                    results['summary']['status'] = 'INTERRUPTED'
                    save_and_exit(results)
                    return
                except Exception as e:
                    print_fail(f"카메라 점검 중 오류 발생: {str(e)}")
                    results['cameras'] = {'status': 'ERROR', 'error': str(e)}
                    
                    # 자동 모드면 오류 발생해도 계속 진행
                    if full_auto_mode:
                        print_info("자동 모드: 오류가 발생했지만 계속 진행합니다.")
                        break
                    
                    user_action = ask_continue("오류가 발생했습니다. 계속 진행하시겠습니까?")
                    if user_action == 'quit':
                        save_and_exit(results)
                        return
                    elif user_action == 'retry':
                        print_info("카메라 점검을 다시 수행합니다...")
                        continue  # 루프 계속 (재시도)
                    else:
                        break  # 루프 탈출 (계속 진행)
        else:
            if camera_count == 0:
                print_warning("카메라 점검을 건너뜁니다 (카메라 개수: 0)")
                results['cameras'] = {'status': 'SKIP', 'total': 0}
                progress.update(1, "카메라 점검 건너뜀")
    else:
        print_info("카메라 점검을 건너뜁니다 (선택되지 않음)")
        results['cameras'] = {'status': 'SKIP', 'reason': 'Not selected'}
    
    # ========== 3. PostgreSQL 점검 ========== (현재 비활성화)
    # try:
    #     pg_result = check_postgresql(config['pg'])
    #     results['postgresql'] = pg_result
    #     
    #     # 사용자 컨펌
    #     user_action = ask_continue("PostgreSQL 점검 완료. 다음 단계로 진행하시겠습니까?")
    #     if user_action == 'quit':
    #         print_warning("사용자가 점검을 중단했습니다.")
    #         results['summary']['status'] = 'QUIT'
    #         save_and_exit(results)
    #         return
    #     elif user_action == 'skip':
    #         print_warning("다음 단계를 건너뜁니다.")
    # 
    # except KeyboardInterrupt:
    #     print("")
    #     print_warning("사용자가 점검을 중단했습니다.")
    #     results['summary']['status'] = 'INTERRUPTED'
    #     save_and_exit(results)
    #     return
    # except Exception as e:
    #     print_fail(f"PostgreSQL 점검 중 오류 발생: {str(e)}")
    #     results['postgresql'] = {'status': 'ERROR', 'error': str(e)}
    #     
    #     user_action = ask_continue("오류가 발생했습니다. 계속 진행하시겠습니까?")
    #     if user_action == 'quit':
    #         save_and_exit(results)
    #         return
    
    # ========== 3. NAS 점검 ==========
    if 'nas' in selected_checks:
    while True:
        try:
            nas_result = check_nas_status(config['nas'])
            results['nas'] = nas_result
            progress.update(1, "NAS 점검 완료")
            
            # 자동 모드면 확인 없이 계속 진행
            if full_auto_mode:
                print_info("자동 모드: 다음 단계로 진행합니다.")
                break
            
            # 사용자 컨펌
            user_action = ask_continue("NAS 점검 완료. 다음 단계로 진행하시겠습니까?")
            if user_action == 'quit':
                print_warning("사용자가 점검을 중단했습니다.")
                results['summary']['status'] = 'QUIT'
                save_and_exit(results)
                return
            elif user_action == 'retry':
                print_info("NAS 점검을 다시 수행합니다...")
                continue  # 루프 계속 (재시도)
            else:
                break  # 루프 탈출 (계속 진행)
        
        except KeyboardInterrupt:
            print("")
            print_warning("사용자가 점검을 중단했습니다.")
            results['summary']['status'] = 'INTERRUPTED'
            save_and_exit(results)
            return
        except Exception as e:
            print_fail(f"NAS 점검 중 오류 발생: {str(e)}")
            results['nas'] = {'status': 'ERROR', 'error': str(e)}
            
            # 자동 모드면 오류 발생해도 계속 진행
            if full_auto_mode:
                print_info("자동 모드: 오류가 발생했지만 계속 진행합니다.")
                break
            
            user_action = ask_continue("오류가 발생했습니다. 계속 진행하시겠습니까?")
            if user_action == 'quit':
                save_and_exit(results)
                return
            elif user_action == 'retry':
                print_info("NAS 점검을 다시 수행합니다...")
                continue  # 루프 계속 (재시도)
            else:
                break  # 루프 탈출 (계속 진행)
    else:
        print_info("NAS 점검을 건너뜁니다 (선택되지 않음)")
        results['nas'] = {'status': 'SKIP', 'reason': 'Not selected'}
    
    # ========== 4. 시스템 종합 점검 ==========
    if 'system' in selected_checks:
    try:
        system_result = check_system_status()
        results['system'] = system_result
            progress.finish("모든 점검 완료")
        
        print("")
        print_info("모든 점검이 완료되었습니다!")
    
    except KeyboardInterrupt:
        print("")
        print_warning("사용자가 점검을 중단했습니다.")
        results['summary']['status'] = 'INTERRUPTED'
        save_and_exit(results)
        return
    except Exception as e:
        print_fail(f"시스템 종합 점검 중 오류 발생: {str(e)}")
        results['system'] = {'status': 'ERROR', 'error': str(e)}
    else:
        print_info("시스템 점검을 건너뜁니다 (선택되지 않음)")
        results['system'] = {'status': 'SKIP', 'reason': 'Not selected'}
    
    # ========== 최종 요약 ==========
    generate_summary(results)
    print_final_summary_table(results)
    
    # CLI 인자에서 출력 포맷과 디렉토리 가져오기
    output_formats = cli_args.output_format if 'cli_args' in locals() else ['txt', 'json', 'html']
    output_dir = cli_args.output_dir if 'cli_args' in locals() else "."
    save_and_exit(results, output_formats=output_formats, output_dir=output_dir)


def generate_summary(results: dict):
    """최종 요약 생성"""
    summary = {}
    
    # UPS
    if 'ups' in results:
        summary['UPS/NUT'] = results['ups'].get('status', 'UNKNOWN')
    
    # 카메라
    if 'cameras' in results:
        cam = results['cameras']
        summary['카메라'] = f"{cam.get('status', 'UNKNOWN')} (PASS: {cam.get('pass_count', 0)}, FAIL: {cam.get('fail_count', 0)}, SKIP: {cam.get('skip_count', 0)})"
    
    # PostgreSQL (비활성화)
    # if 'postgresql' in results:
    #     summary['PostgreSQL'] = results['postgresql'].get('status', 'UNKNOWN')
    
    # NAS
    if 'nas' in results:
        summary['NAS'] = results['nas'].get('status', 'UNKNOWN')
    
    # 시스템
    if 'system' in results:
        summary['시스템'] = results['system'].get('status', 'UNKNOWN')
    
    results['summary'] = summary


def print_final_summary_table(results: dict):
    """최종 점검 결과를 한눈에 볼 수 있는 테이블로 출력"""
    from utils.ui import Colors, print_header, print_table
    
    print("")
    print_header("최종 점검 결과 요약")
    
    # ===== 1. 전체 요약 =====
    print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
    print(f"  전체 요약")
    print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
    
    summary_items = [
        ("UPS/NUT", results.get('summary', {}).get('UPS/NUT', 'UNKNOWN')),
        ("카메라", results.get('summary', {}).get('카메라', 'UNKNOWN')),
        # ("PostgreSQL", results.get('summary', {}).get('PostgreSQL', 'UNKNOWN')),  # 비활성화
        ("NAS", results.get('summary', {}).get('NAS', 'UNKNOWN')),
        ("시스템", results.get('summary', {}).get('시스템', 'UNKNOWN'))
    ]
    
    for item, status in summary_items:
        # 카메라는 상세 정보가 포함된 문자열 파싱
        if item == "카메라":
            # "FAIL (PASS: 0, FAIL: 1, SKIP: 0)" 형태에서 상태만 추출
            status_only = status.split(' ')[0] if ' ' in status else status
            
            if status_only == 'PASS':
                status_str = f"{Colors.PASS}✓{Colors.RESET} {status}"
            elif status_only == 'FAIL':
                status_str = f"{Colors.FAIL}✗{Colors.RESET} {status}"
            elif status_only == 'SKIP':
                status_str = f"{Colors.SKIP}⊘{Colors.RESET} {status}"
            else:
                status_str = f"{Colors.WARNING}{status}{Colors.RESET}"
        else:
            # 다른 항목들
            if status == 'PASS':
                status_str = f"{Colors.PASS}✓{Colors.RESET} {status}"
            elif status == 'FAIL':
                status_str = f"{Colors.FAIL}✗{Colors.RESET} {status}"
            elif status == 'SKIP':
                status_str = f"{Colors.SKIP}⊘{Colors.RESET} {status}"
            else:
                status_str = f"{Colors.WARNING}{status}{Colors.RESET}"
        
        # 한글 너비를 고려하여 정렬
        padded_item = pad_string(item, 20)
        print(f"  {padded_item} : {status_str}")
    
    print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
    
    # ===== 2. 카메라 상세 결과 =====
    if 'cameras' in results and 'details' in results['cameras']:
        print("")
        print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
        print(f"  카메라 상세 결과")
        print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
        
        camera_details = results['cameras']['details']
        
        # 테이블 헤더 (한글 너비 고려)
        header_camera = pad_string("카메라", 12)
        header_ip = pad_string("IP", 17)
        header_source = pad_string("원본", 10)
        header_blur = pad_string("블러", 10)
        header_log = pad_string("로그", 10)
        print(f"  {header_camera} {header_ip} {header_source} {header_blur} {header_log}")
        
        for cam in camera_details:
            name = cam.get('name', 'Unknown')
            ip = cam.get('ip', 'N/A')
            source = cam.get('source_status', 'UNKNOWN')
            mediamtx = cam.get('mediamtx_status', 'UNKNOWN')
            log = cam.get('log_status', 'UNKNOWN')
            
            # 상태 색상 처리
            if source == 'PASS':
                source_str = f"{Colors.PASS}{source}{Colors.RESET}"
            elif source == 'FAIL':
                source_str = f"{Colors.FAIL}{source}{Colors.RESET}"
            else:
                source_str = f"{Colors.SKIP}{source}{Colors.RESET}"
            
            if mediamtx == 'PASS':
                mediamtx_str = f"{Colors.PASS}{mediamtx}{Colors.RESET}"
            elif mediamtx == 'FAIL':
                mediamtx_str = f"{Colors.FAIL}{mediamtx}{Colors.RESET}"
            else:
                mediamtx_str = f"{Colors.SKIP}{mediamtx}{Colors.RESET}"
            
            if log == 'PASS':
                log_str = f"{Colors.PASS}{log}{Colors.RESET}"
            elif log == 'FAIL':
                log_str = f"{Colors.FAIL}{log}{Colors.RESET}"
            else:
                log_str = f"{Colors.SKIP}{log}{Colors.RESET}"
            
            # 한글 너비를 고려하여 정렬
            padded_name = pad_string(name, 12)
            padded_ip = pad_string(ip, 17)
            padded_source = pad_string(source_str, 10)
            padded_blur = pad_string(mediamtx_str, 10)
            padded_log = pad_string(log_str, 10)
            print(f"  {padded_name} {padded_ip} {padded_source} {padded_blur} {padded_log}")
        
        print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
        
        # 카메라 통계
        cam_stats = results['cameras']
        print("")
        print(f"  스트림 점검: "
              f"{Colors.PASS}PASS {cam_stats.get('pass_count', 0)}{Colors.RESET}, "
              f"{Colors.FAIL}FAIL {cam_stats.get('fail_count', 0)}{Colors.RESET}, "
              f"{Colors.SKIP}SKIP {cam_stats.get('skip_count', 0)}{Colors.RESET}")
        
        # 영상 파일 확인 결과
        if 'video_files' in results['cameras']:
            video_files = results['cameras']['video_files']
            video_status = video_files.get('status', 'UNKNOWN')
            
            if video_status == 'PASS':
                status_str = f"{Colors.PASS}✓ 영상 파일 저장 완료{Colors.RESET}"
            elif video_status == 'FAIL':
                missing = video_files.get('missing_videos', [])
                status_str = f"{Colors.FAIL}✗ 영상 파일 누락 (카메라 {missing}){Colors.RESET}"
            else:
                status_str = f"{Colors.WARNING}영상 파일 확인 안 됨{Colors.RESET}"
            
            print(f"  영상 파일: {status_str}")
    
    # ===== 3. 시스템 점검 상세 결과 =====
    if 'system' in results and results['system'].get('status') != 'UNKNOWN':
        print("")
        print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
        print(f"  시스템 점검 상세 결과")
        print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
        
        system = results['system']
        
        # 서비스 상태
        if 'services' in system:
            # 헤더 (한글 너비 고려)
            header_service = pad_string("서비스 상태", 20)
            header_state = pad_string("상태", 15)
            header_result = pad_string("판정", 10)
            print(f"  {header_service} {header_state} {header_result}")
            
            for service, info in system['services'].items():
                if isinstance(info, dict):
                    service_name = info.get('service', service)[:20]
                    state = info.get('state', 'unknown')[:15]
                    status = info.get('status', 'UNKNOWN')
                    
                    if status == 'PASS':
                        status_str = f"{Colors.PASS}PASS{Colors.RESET}"
                    elif status == 'FAIL':
                        status_str = f"{Colors.FAIL}FAIL{Colors.RESET}"
                    elif status == 'SKIP':
                        status_str = f"{Colors.SKIP}SKIP{Colors.RESET}"
                    else:
                        status_str = f"{Colors.WARNING}WARN{Colors.RESET}"
                    
                    # 한글 너비를 고려하여 정렬
                    padded_service = pad_string(service_name, 20)
                    padded_state = pad_string(state, 15)
                    padded_status = pad_string(status_str, 10)
                    print(f"  {padded_service} {padded_state} {padded_status}")
        
        # 포트 리스닝
        if 'ports' in system:
            # 헤더 (한글 너비 고려)
            header_port = pad_string("포트 리스닝", 20)
            header_listen_state = pad_string("상태", 15)
            header_listen_result = pad_string("판정", 10)
            print(f"  {header_port} {header_listen_state} {header_listen_result}")
            
            for port_name, info in system['ports'].items():
                if isinstance(info, dict):
                    port_display = port_name[:20]
                    listening_status = "Listening" if info.get('listening') else "Not listening"
                    status = info.get('status', 'UNKNOWN')
                    
                    if info.get('listening'):
                        status_str = f"{Colors.PASS}PASS{Colors.RESET}"
                    else:
                        status_str = f"{Colors.FAIL}FAIL{Colors.RESET}"
                    
                    # 한글 너비를 고려하여 정렬
                    padded_port = pad_string(port_display, 20)
                    padded_listen = pad_string(listening_status, 15)
                    padded_port_status = pad_string(status_str, 10)
                    print(f"  {padded_port} {padded_listen} {padded_port_status}")
        
        # 통계
        if 'summary' in system:
            summary = system['summary']
            header_summary = pad_string("점검 통계", 76)
            print(f"  {header_summary}")
            print(f"    {Colors.PASS}PASS: {summary.get('pass_count', 0)}{Colors.RESET}, "
                  f"{Colors.FAIL}FAIL: {summary.get('fail_count', 0)}{Colors.RESET}, "
                  f"{Colors.WARNING}WARN: {summary.get('warn_count', 0)}{Colors.RESET}, "
                  f"{Colors.SKIP}SKIP: {summary.get('skip_count', 0)}{Colors.RESET}")
        
        print(f"{Colors.INFO}{'═' * 80}{Colors.RESET}")
    
    print("")


def save_and_exit(results: dict, output_formats: list = None, output_dir: str = "."):
    """결과 저장 및 종료"""
    from utils.ui import print_info, print_pass
    
    print("")
    print_summary(results)
    
    # 리포트 저장 (지정된 포맷만)
    if output_formats is None:
        output_formats = ['txt', 'json', 'html']
    
    report_files = []
    
    if 'txt' in output_formats:
        try:
            txt_file = save_report(results, output_dir=output_dir)
            report_files.append(f"TXT: {txt_file}")
        except Exception as e:
            print_fail(f"TXT 리포트 저장 실패: {str(e)}")
    
    if 'json' in output_formats:
        try:
            json_file = save_json_report(results, output_dir=output_dir)
            report_files.append(f"JSON: {json_file}")
        except Exception as e:
            print_fail(f"JSON 리포트 저장 실패: {str(e)}")
    
    if 'html' in output_formats:
        try:
            html_file = save_html_report(results, output_dir=output_dir)
            report_files.append(f"HTML: {html_file}")
        except Exception as e:
            print_fail(f"HTML 리포트 저장 실패: {str(e)}")
    
    if report_files:
        print("")
        print_pass("리포트 저장 완료:")
        for file_info in report_files:
            print(f"  {file_info}")
    
    print("")
    print_info("점검을 종료합니다.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("")
        print_warning("프로그램이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print_fail(f"예상치 못한 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

