"""
카메라 RTSP 연결 점검 모듈
OpenCV를 사용하여 RTSP 스트림을 실시간으로 확인
+ 카메라 영상 저장 로그 자동 점검
+ 영상 파일 존재 여부 확인
"""
import cv2
import time
import gc
import os
import re
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# OpenCV/FFmpeg 에러 메시지 완전히 숨기기 (H.264, HEVC 등 모든 디코딩 경고 제거)
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp|fflags;nobuffer'
os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'  # AV_LOG_QUIET (-8) = 완전 침묵
cv2.setLogLevel(0)  # OpenCV 로그 레벨을 0으로 설정 (에러 숨김)


def generate_camera_urls(
    camera_count: int,
    base_ip: str = "192.168.1",
    start_ip: int = 101,
    username: str = "root",
    password: str = "root",
    rtsp_path: str = "cam0_0",
    rtsp_port: int = 554,
    mediamtx_base_port: int = 1111
) -> List[Dict[str, Any]]:
    """카메라 RTSP URL 생성 (원본 + 블러 처리 스트리밍)"""
    cameras = []
    
    for i in range(camera_count):
        camera_num = i + 1
        ip_last_octet = start_ip + i
        ip_address = f"{base_ip}.{ip_last_octet}"
        
        # 원본 카메라 RTSP URL
        source_rtsp_url = f"rtsp://{username}:{password}@{ip_address}:{rtsp_port}/{rtsp_path}"
        
        # 블러 처리된 MediaMTX 스트리밍 URL (포트: 1111, 1112, 1113, ...)
        mediamtx_port = mediamtx_base_port + i
        mediamtx_rtsp_url = f"rtsp://127.0.0.1:{mediamtx_port}/live"
        
        camera_info = {
            "name": f"카메라 {camera_num}",
            "camera_num": camera_num,
            "ip": ip_address,
            "source_url": source_rtsp_url,
            "mediamtx_url": mediamtx_rtsp_url,
            "mediamtx_port": mediamtx_port
        }
        cameras.append(camera_info)
    
    return cameras


def test_camera_connection(rtsp_url: str, timeout: int = 10) -> Dict[str, Any]:
    """카메라 연결 테스트 (OpenCV)"""
    cap = None
    try:
        cap = cv2.VideoCapture(rtsp_url)
        
        # 연결 타임아웃 설정
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
        
        if not cap.isOpened():
            return {
                'success': False,
                'error': 'Failed to open RTSP stream'
            }
        
        # 첫 프레임 읽기
        ret, frame = cap.read()
        
        if not ret or frame is None:
            return {
                'success': False,
                'error': 'Failed to read frame'
            }
        
        # 프레임 정보
        height, width = frame.shape[:2]
        
        return {
            'success': True,
            'width': width,
            'height': height,
            'frame': frame
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if cap is not None:
            cap.release()


def find_latest_log_file(camera_num: int, log_base_path: str, search_days: int = 1) -> Optional[str]:
    """
    최근 로그 파일을 자동으로 찾기 (오늘부터 최근 N일간 검색)
    경로 구조: /mnt/nas/logs/년/월/일/rtsp_streamX_YYYYMMDD.log
    
    Args:
        camera_num: 카메라 번호
        log_base_path: 로그 베이스 경로 (예: /mnt/nas/logs)
        search_days: 검색할 일수 (기본 1일 - 오늘과 어제)
    
    Returns:
        로그 파일 경로 또는 None
    """
    now = datetime.now()
    
    # 오늘부터 과거로 검색 (년/월/일 구조, 시간 폴더 없음)
    for days_ago in range(search_days + 1):  # 오늘 + search_days 전까지
        search_date = now - timedelta(days=days_ago)
        year = search_date.strftime("%Y")
        month = search_date.strftime("%m")
        day = search_date.strftime("%d")
        log_date = search_date.strftime("%Y%m%d")
        
        # 날짜 폴더 경로
        log_dir = os.path.join(log_base_path, year, month, day)
        
        if not os.path.exists(log_dir):
            continue
        
        # 해당 날짜 폴더에서 카메라 로그 파일 찾기
        # 파일명 패턴: rtsp_stream{camera_num}_YYYYMMDD.log
        log_file = os.path.join(log_dir, f"rtsp_stream{camera_num}_{log_date}.log")
        
        if os.path.exists(log_file):
            return log_file
    
    return None


def check_camera_log(camera_num: int, log_base_path: str = "/mnt/nas/logs") -> Dict[str, Any]:
    """
    카메라 영상 저장 로그 확인
    경로 구조: /mnt/nas/logs/년/월/일/시간/
    
    Args:
        camera_num: 카메라 번호 (1, 2, 3, ...)
        log_base_path: 로그 베이스 경로 (기본값: /mnt/nas/logs)
    
    Returns:
        로그 점검 결과 딕셔너리
    """
    from utils.ui import print_info, print_pass, print_fail, print_warning
    
    result = {
        'checked': False,
        'log_found': False,
        'status': 'UNKNOWN',
        'details': {}
    }
    
    # 로그 파일 자동 검색 (오늘과 어제)
    print_info(f"카메라 {camera_num} 로그 파일 검색 중...")
    log_file = find_latest_log_file(camera_num, log_base_path, search_days=1)
    
    # 로그 파일 존재 확인
    if not log_file:
        print_warning(f"로그 파일을 찾을 수 없습니다 (검색 경로: {log_base_path})")
        print_warning("오늘과 어제 로그가 없습니다")
        result['status'] = 'SKIP'
        result['details']['message'] = '로그 파일 없음 (오늘/어제)'
        return result
    
    print_info(f"로그 파일 발견: {log_file}")
    
    result['log_found'] = True
    result['checked'] = True
    
    # 현재 시간 (시간 검증용)
    now = datetime.now()
    
    try:
        # 로그 파일에서 최근 "영상 저장 완료" 항목 찾기
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 역순으로 읽어서 최근 영상 저장 로그 찾기
        last_save_info = None
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if '영상 저장 완료:' in line:
                # 타임스탬프 추출
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    log_time_str = timestamp_match.group(1)
                    log_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
                    
                    # 다음 3줄에서 프레임 수, 영상 길이, 파일 크기 추출
                    frame_count = None
                    video_length = None
                    file_size = None
                    
                    if i + 1 < len(lines):
                        frame_line = lines[i + 1]
                        frame_match = re.search(r'프레임 수:\s*(\d+)', frame_line)
                        if frame_match:
                            frame_count = int(frame_match.group(1))
                    
                    if i + 2 < len(lines):
                        length_line = lines[i + 2]
                        length_match = re.search(r'영상 길이:\s*([\d.]+)초', length_line)
                        if length_match:
                            video_length = float(length_match.group(1))
                    
                    if i + 3 < len(lines):
                        size_line = lines[i + 3]
                        size_match = re.search(r'파일 크기:\s*([\d.]+)MB', size_line)
                        if size_match:
                            file_size = float(size_match.group(1))
                    
                    last_save_info = {
                        'log_time': log_time,
                        'frame_count': frame_count,
                        'video_length': video_length,
                        'file_size': file_size
                    }
                    break
        
        if not last_save_info:
            print_warning("로그에서 '영상 저장 완료' 기록을 찾을 수 없습니다")
            result['status'] = 'FAIL'
            result['details']['message'] = '영상 저장 로그 없음'
            return result
        
        # 결과 저장
        result['details'] = last_save_info
        
        # 검증 시작
        print("")
        print(f"  최근 영상 저장 시각: {last_save_info['log_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  프레임 수: {last_save_info['frame_count']}")
        print(f"  영상 길이: {last_save_info['video_length']}초")
        print(f"  파일 크기: {last_save_info['file_size']}MB")
        print("")
        
        # 1. 시간 검증 (10분 이내)
        time_diff = now - last_save_info['log_time']
        time_diff_minutes = time_diff.total_seconds() / 60
        
        if time_diff_minutes > 10:
            print_fail(f"시간 검증 실패: 로그가 {time_diff_minutes:.1f}분 전 (기준: 10분 이내)")
            result['status'] = 'FAIL'
            result['details']['fail_reason'] = f'로그 시간 초과 ({time_diff_minutes:.1f}분)'
            return result
        else:
            print_pass(f"시간 검증 통과: {time_diff_minutes:.1f}분 전")
        
        # 2. 프레임 수 검증 (4400~4600)
        if last_save_info['frame_count'] is None:
            print_warning("프레임 수 정보 없음")
            result['status'] = 'FAIL'
            result['details']['fail_reason'] = '프레임 수 정보 없음'
            return result
        
        if 4400 <= last_save_info['frame_count'] <= 4600:
            print_pass(f"프레임 수 검증 통과: {last_save_info['frame_count']} (기준: 4400~4600)")
        else:
            print_fail(f"프레임 수 검증 실패: {last_save_info['frame_count']} (기준: 4400~4600)")
            result['status'] = 'FAIL'
            result['details']['fail_reason'] = f'프레임 수 범위 벗어남 ({last_save_info["frame_count"]})'
            return result
        
        # 3. 영상 길이 검증 (280~310초)
        if last_save_info['video_length'] is None:
            print_warning("영상 길이 정보 없음")
            result['status'] = 'FAIL'
            result['details']['fail_reason'] = '영상 길이 정보 없음'
            return result
        
        if 280 <= last_save_info['video_length'] <= 310:
            print_pass(f"영상 길이 검증 통과: {last_save_info['video_length']}초 (기준: 280~310초)")
        else:
            print_fail(f"영상 길이 검증 실패: {last_save_info['video_length']}초 (기준: 280~310초)")
            result['status'] = 'FAIL'
            result['details']['fail_reason'] = f'영상 길이 범위 벗어남 ({last_save_info["video_length"]}초)'
            return result
        
        # 모든 검증 통과
        result['status'] = 'PASS'
        print("")
        print_pass("로그 검증 완료: 모든 기준 충족")
        
    except Exception as e:
        print_fail(f"로그 파일 읽기 오류: {str(e)}")
        result['status'] = 'FAIL'
        result['details']['error'] = str(e)
    
    return result


def show_camera_stream(camera_info: Dict[str, Any], stream_type: str = "source", auto_mode: bool = False) -> str:
    """
    카메라 스트림을 OpenCV 창으로 표시하고 사용자 입력 대기
    또는 자동 모드로 프레임 읽기만 확인
    
    Args:
        camera_info: 카메라 정보
        stream_type: "source" (원본) 또는 "mediamtx" (블러 처리)
        auto_mode: True면 영상 표시 없이 자동 검증
    
    Returns: 'pass', 'fail', 'skip', 'quit'
    """
    from utils.ui import print_info, print_warning, print_fail, print_pass, ask_camera_result
    
    name = camera_info['name']
    
    if stream_type == "source":
        url = camera_info['source_url']
        stream_label = "원본 카메라"
        window_name = f"{name} - 원본 RTSP"
    else:
        url = camera_info['mediamtx_url']
        stream_label = f"블러 처리 스트리밍 (포트 {camera_info['mediamtx_port']})"
        window_name = f"{name} - 블러 처리 RTSP"
    
    print_info(f"{name} {stream_label} 연결 시도 중...")
    if stream_type == "source":
        print_info(f"  URL: {camera_info['ip']}:554")
    else:
        print_info(f"  URL: 127.0.0.1:{camera_info['mediamtx_port']}")
    
    # 연결 테스트 (타임아웃: 10초)
    test_result = test_camera_connection(url, timeout=10)
    
    if not test_result['success']:
        print_fail(f"{name} {stream_label} 연결 실패: {test_result['error']}")
        print_warning("자동으로 FAIL 처리됩니다.")
        return 'fail'
    
    print_pass(f"{name} {stream_label} 연결 성공!")
    print_info(f"  해상도: {test_result['width']}x{test_result['height']}")
    
    # Auto 모드: 프레임 읽기만 확인하고 자동 PASS
    if auto_mode:
        print_pass(f"  프레임 읽기 성공 → 자동 PASS")
        return 'pass'
    
    # 스트림 표시
    cap = None
    try:
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
        
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 800, 600)
        
        print_info("영상이 표시됩니다. 확인 후 키를 눌러주세요:")
        print("  [p] PASS  [f] FAIL  [s] SKIP  [q] 종료")
        print("  (영상 창이 활성화된 상태에서 키를 누르세요)")
        
        # 프레임 표시 루프
        frame_count = 0
        max_frames = 300  # 약 10초 (30fps 기준)
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            
            if not ret or frame is None:
                print_warning("프레임 읽기 실패")
                break
            
            # 화면에 정보 표시
            text_lines = [
                f"{name} - {stream_label}",
                f"Port: {camera_info['mediamtx_port']}" if stream_type == "mediamtx" else f"IP: {camera_info['ip']}",
                "Press: [p]PASS [f]FAIL [s]SKIP [q]QUIT"
            ]
            
            y_offset = 30
            for line in text_lines:
                cv2.putText(frame, line, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                y_offset += 30
            
            cv2.imshow(window_name, frame)
            
            # 키 입력 대기 (30ms)
            key = cv2.waitKey(30) & 0xFF
            
            if key == ord('p'):
                cv2.destroyAllWindows()
                return 'pass'
            elif key == ord('f'):
                cv2.destroyAllWindows()
                return 'fail'
            elif key == ord('s'):
                cv2.destroyAllWindows()
                return 'skip'
            elif key == ord('q'):
                cv2.destroyAllWindows()
                return 'quit'
            elif key == 27:  # ESC
                cv2.destroyAllWindows()
                return 'quit'
            
            frame_count += 1
        
        # 타임아웃 - 사용자 입력을 콘솔에서 받기
        cv2.destroyAllWindows()
        print_warning("영상 표시 시간 초과. 콘솔에서 결과를 입력하세요.")
        return ask_camera_result(f"{name} {stream_label}")
    
    except Exception as e:
        print_fail(f"스트림 표시 중 오류: {str(e)}")
        cv2.destroyAllWindows()
        return 'fail'
    
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        # 메모리 정리를 위해 약간의 대기 및 가비지 컬렉션
        time.sleep(0.1)
        gc.collect()


def check_video_files(camera_count: int, video_base_path: str = "/mnt/nas/cam") -> Dict[str, Any]:
    """
    영상 파일 존재 여부 확인
    경로 구조: /mnt/nas/cam/년/월/일/시간/
    
    Args:
        camera_count: 카메라 개수
        video_base_path: 영상 파일 베이스 경로 (기본값: /mnt/nas/cam)
    
    Returns:
        영상 파일 점검 결과 딕셔너리
    """
    from utils.ui import print_info, print_pass, print_fail, print_warning
    
    result = {
        'checked': True,
        'status': 'UNKNOWN',
        'found_videos': [],
        'missing_videos': []
    }
    
    print("")
    print("=" * 80)
    print("   영상 파일 저장 확인")
    print("=" * 80)
    print_info(f"영상 파일 저장 확인 중... (카메라 {camera_count}대)")
    
    now = datetime.now()
    
    # 최근 10분 내 파일 검색 (날짜 경계를 고려하여 폴더 경로 생성)
    found_files = {}
    
    # 검색할 폴더 목록 생성 (현재 시각부터 10분 전까지)
    search_dirs = set()
    for minutes_ago in range(0, 11):  # 0~10분 전
        check_time = now - timedelta(minutes=minutes_ago)
        date_path = check_time.strftime("%Y/%m/%d/%H")
        video_dir = os.path.join(video_base_path, date_path)
        if os.path.exists(video_dir):
            search_dirs.add(video_dir)
    
    # 검색할 폴더들을 확인
    for video_dir in sorted(search_dirs, reverse=True):
        print_info(f"폴더 확인 중: {video_dir}")
        
        # 각 카메라의 영상 파일 찾기
        for cam_num in range(1, camera_count + 1):
            if cam_num in found_files:
                continue  # 이미 찾았으면 스킵
            
            # 파일 패턴: *_stream0{cam_num}_*.mp4
            pattern = os.path.join(video_dir, f"*_stream0{cam_num}_*.mp4")
            files = glob.glob(pattern)
            
            if files:
                # 가장 최근 파일 찾기
                latest_file = max(files, key=os.path.getmtime)
                mtime = os.path.getmtime(latest_file)
                file_time = datetime.fromtimestamp(mtime)
                time_diff = (now - file_time).total_seconds() / 60
                
                # 10분 이내 파일만 인정
                if time_diff <= 10:
                    found_files[cam_num] = {
                        'path': latest_file,
                        'time': file_time,
                        'minutes_ago': time_diff
                    }
    
    # 결과 정리
    print("")
    for cam_num in range(1, camera_count + 1):
        if cam_num in found_files:
            file_info = found_files[cam_num]
            result['found_videos'].append(cam_num)
            print_pass(f"카메라 {cam_num} 영상 발견: {os.path.basename(file_info['path'])} ({file_info['minutes_ago']:.1f}분 전)")
        else:
            result['missing_videos'].append(cam_num)
            print_fail(f"카메라 {cam_num} 영상 없음 (최근 10분 내)")
    
    # 전체 판정
    print("")
    if len(result['missing_videos']) == 0:
        result['status'] = 'PASS'
        print_pass(f"영상 파일 확인 완료: 모든 카메라 영상 저장됨 ({camera_count}개)")
    else:
        result['status'] = 'FAIL'
        print_fail(f"영상 파일 확인 실패: {len(result['missing_videos'])}대 영상 없음 (카메라 {result['missing_videos']})")
    
    return result


def check_cameras(camera_count: int, camera_config: Dict[str, str], auto_mode: bool = False) -> Dict[str, Any]:
    """전체 카메라 점검 실행 (원본 + 블러 처리 스트리밍)"""
    from utils.ui import (
        print_section, print_pass, print_fail, print_skip,
        print_info, print_warning
    )
    
    print_section(2, 4, "카메라 RTSP 연결 점검")
    
    # 모드 표시
    if auto_mode:
        print_info("📡 Auto 모드: 영상 표시 없이 스트림 상태만 자동 확인합니다.")
    else:
        print_info("🖥️  GUI 모드: 각 카메라 영상을 확인하고 판정해주세요.")
    
    # 카메라 URL 생성
    cameras = generate_camera_urls(
        camera_count=camera_count,
        base_ip=camera_config.get('base_ip', '192.168.1'),
        start_ip=int(camera_config.get('start_ip', 101)),
        username=camera_config.get('username', 'root'),
        password=camera_config.get('password', 'root'),
        rtsp_path=camera_config.get('rtsp_path', 'cam0_0'),
        rtsp_port=int(camera_config.get('rtsp_port', 554)),
        mediamtx_base_port=int(camera_config.get('mediamtx_base_port', 1111))
    )
    
    print_info(f"총 {camera_count}대의 카메라를 점검합니다.")
    if not auto_mode:
        print_info("각 카메라마다 원본 영상, 블러 처리 스트리밍, 영상 저장 로그를 확인합니다.")
    print("")
    
    results = {
        'total': camera_count,
        'pass_count': 0,
        'fail_count': 0,
        'skip_count': 0,
        'details': []
    }
    
    # 각 카메라 순차 점검
    for camera in cameras:
        print("")
        print("=" * 80)
        print(f"   {camera['name']} 점검")
        print("=" * 80)
        
        camera_result = {
            'name': camera['name'],
            'ip': camera['ip'],
            'mediamtx_port': camera['mediamtx_port'],
            'source_status': 'UNKNOWN',
            'mediamtx_status': 'UNKNOWN',
            'log_status': 'UNKNOWN',
            'log_details': {}
        }
        
        # 1) 원본 카메라 영상 확인
        print("")
        print(f"[1/2] {camera['name']} - 원본 카메라 영상")
        print("-" * 80)
        source_decision = show_camera_stream(camera, stream_type="source", auto_mode=auto_mode)
        camera_result['source_status'] = source_decision.upper()
        
        if source_decision == 'quit':
            print_warning("사용자가 점검을 중단했습니다.")
            results['details'].append(camera_result)
            results['status'] = 'QUIT'
            return results
        
        # 2) 블러 처리 스트리밍 확인
        print("")
        print(f"[2/2] {camera['name']} - 블러 처리 스트리밍")
        print("-" * 80)
        mediamtx_decision = show_camera_stream(camera, stream_type="mediamtx", auto_mode=auto_mode)
        camera_result['mediamtx_status'] = mediamtx_decision.upper()
        
        if mediamtx_decision == 'quit':
            print_warning("사용자가 점검을 중단했습니다.")
            results['details'].append(camera_result)
            results['status'] = 'QUIT'
            return results
        
        # 3) 카메라 로그 확인 (자동)
        print("")
        print(f"[3/3] {camera['name']} - 영상 저장 로그 확인")
        print("-" * 80)
        log_base_path = camera_config.get('log_base_path', '/mnt/nas/logs')
        log_result = check_camera_log(camera['camera_num'], log_base_path)
        camera_result['log_status'] = log_result['status']
        camera_result['log_details'] = log_result.get('details', {})
        
        # 결과 기록
        results['details'].append(camera_result)
        
        # 전체 상태 판정 (두 스트림 + 로그 모두 고려)
        log_status = camera_result['log_status']
        
        if source_decision == 'pass' and mediamtx_decision == 'pass' and log_status == 'PASS':
            results['pass_count'] += 1
            print("")
            print_pass(f"{camera['name']}: PASS (원본 ✓, 블러 처리 ✓, 로그 ✓)")
        elif source_decision == 'skip' or mediamtx_decision == 'skip':
            results['skip_count'] += 1
            print("")
            print_skip(f"{camera['name']}: SKIP")
        else:
            results['fail_count'] += 1
            print("")
            fail_reasons = []
            if source_decision != 'pass':
                fail_reasons.append(f"원본: {source_decision}")
            if mediamtx_decision != 'pass':
                fail_reasons.append(f"블러: {mediamtx_decision}")
            if log_status != 'PASS':
                fail_reasons.append(f"로그: {log_status}")
            print_fail(f"{camera['name']}: FAIL ({', '.join(fail_reasons)})")
        
        # 메모리 정리 (다음 카메라로 이동 전)
        cv2.destroyAllWindows()
        time.sleep(0.5)
        gc.collect()
    
    # 전체 상태 판정
    print("")
    print("=" * 80)
    print_info(f"카메라 점검 완료: PASS {results['pass_count']}, FAIL {results['fail_count']}, SKIP {results['skip_count']}")
    
    if results['fail_count'] == 0 and results['pass_count'] > 0:
        results['status'] = 'PASS'
        print_pass("카메라 점검 결과: PASS")
    elif results['fail_count'] > 0:
        results['status'] = 'FAIL'
        print_fail(f"카메라 점검 결과: FAIL ({results['fail_count']}대 실패)")
    else:
        results['status'] = 'SKIP'
        print_skip("카메라 점검 결과: SKIP")
    
    # 최종 메모리 정리
    cv2.destroyAllWindows()
    gc.collect()
    
    # ========== 영상 파일 저장 확인 ==========
    video_base_path = camera_config.get('video_base_path', '/mnt/nas/cam')
    video_check_result = check_video_files(camera_count, video_base_path)
    results['video_files'] = video_check_result
    
    # 영상 파일 확인 결과를 전체 상태에 반영
    if video_check_result['status'] == 'FAIL':
        print("")
        print_warning("영상 파일 확인 실패로 인해 전체 카메라 점검이 FAIL로 변경됩니다.")
        results['status'] = 'FAIL'
    
    return results

