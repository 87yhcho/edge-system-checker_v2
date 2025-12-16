"""
UPS/NUT 점검 모듈
NUT 서비스 상태, 포트 리스닝, UPS 데이터, 설정 파일, NAS 연결 확인
"""
import os
import subprocess
from typing import Dict, Any


def run_command(cmd: list) -> Dict[str, Any]:
    """명령어 실행 헬퍼"""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timeout',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def check_service_status(service_name: str) -> Dict[str, Any]:
    """systemctl로 서비스 상태 확인"""
    result = run_command(['systemctl', 'is-active', service_name])
    
    status = result['stdout']
    is_active = status == 'active'
    
    return {
        'service': service_name,
        'active': is_active,
        'status': status if status else 'unknown'
    }


def check_nut_services() -> Dict[str, Any]:
    """NUT 관련 서비스들 상태 확인"""
    services = [
        'nut-driver@ups.service',
        'nut-server.service',
        'nut-monitor.service'
        # 'ups-parameters.service'  # 부팅 시에만 실행되는 서비스 (inactive 정상)
    ]
    
    results = {}
    all_active = True
    
    for service in services:
        service_result = check_service_status(service)
        results[service] = service_result['status']
        if not service_result['active']:
            all_active = False
    
    return {
        'details': results,
        'all_active': all_active
    }


def check_port_listening() -> Dict[str, Any]:
    """3493 포트 리스닝 확인"""
    result = run_command(['ss', '-tlnp'])
    
    if result['success']:
        stdout = result['stdout']
        listening = ':3493' in stdout
        
        # 3493 포함된 라인만 추출
        lines = [line for line in stdout.split('\n') if ':3493' in line]
        
        return {
            'listening': listening,
            'details': '\n'.join(lines) if lines else 'No listener found'
        }
    else:
        return {
            'listening': False,
            'details': f"Error: {result['stderr']}"
        }


def check_ups_data(ups_name: str = 'ups') -> Dict[str, Any]:
    """upsc로 UPS 데이터 확인"""
    result = run_command(['upsc', f'{ups_name}@localhost'])
    
    if not result['success']:
        return {
            'success': False,
            'error': result['stderr'] or result['stdout'] or 'Failed to get UPS data',
            'data': {}
        }
    
    # upsc 출력 파싱
    data = {}
    for line in result['stdout'].split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()
    
    # 주요 필드 추출
    important_fields = {
        'ups.status': data.get('ups.status', 'N/A'),
        'battery.charge': data.get('battery.charge', 'N/A'),
        'input.voltage': data.get('input.voltage', 'N/A'),
        'ups.load': data.get('ups.load', 'N/A'),
        'ups.model': data.get('ups.model', 'N/A'),
        'ups.delay.shutdown': data.get('ups.delay.shutdown', 'N/A')
    }
    
    return {
        'success': True,
        'data': important_fields,
        'raw_count': len(data)
    }


def check_config_files() -> Dict[str, bool]:
    """NUT 설정 파일 존재 여부 확인"""
    config_files = [
        '/etc/nut/ups.conf',
        '/etc/nut/upsd.conf',
        '/etc/nut/upsmon.conf',
        '/etc/nut/upssched.conf',
        '/etc/nut/nut.conf'
    ]
    
    results = {}
    for filepath in config_files:
        results[filepath] = os.path.exists(filepath)
    
    return results


def check_ups_status(ups_name: str = 'ups', nas_ip: str = None) -> Dict[str, Any]:
    """전체 UPS 점검 실행"""
    from utils.ui import (
        print_section, print_pass, print_fail, print_info,
        print_warning, print_key_value, print_table
    )
    
    print_section(1, 4, "UPS/NUT 상태 점검")
    
    result = {
        'status': 'UNKNOWN',
        'services': {},
        'port': {},
        'ups_data': {},
        'config_files': {}
    }
    
    # 1. NUT 서비스 상태 확인
    print_info("NUT 서비스 상태 확인 중...")
    services = check_nut_services()
    result['services'] = services['details']
    
    print("")
    for service, status in services['details'].items():
        if status == 'active':
            print_pass(f"{service}: {status}")
        else:
            print_fail(f"{service}: {status}")
    
    # 2. 포트 리스닝 확인
    print("")
    print_info("3493 포트 리스닝 확인 중...")
    port = check_port_listening()
    result['port'] = port
    
    if port['listening']:
        print_pass("NUT 서버가 3493 포트에서 리스닝 중")
        print(f"  {port['details']}")
    else:
        print_fail("NUT 서버가 3493 포트에서 리스닝하지 않음")
        print(f"  {port['details']}")
    
    # 3. UPS 데이터 확인
    print("")
    print_info("UPS 데이터 조회 중...")
    ups_data = check_ups_data(ups_name)
    result['ups_data'] = ups_data
    
    if ups_data['success']:
        print_pass(f"UPS 데이터 조회 성공 (총 {ups_data['raw_count']}개 필드)")
        print("")
        print("  주요 UPS 정보:")
        
        # 테이블 형식으로 출력
        headers = ["항목", "값"]
        rows = [[k, v] for k, v in ups_data['data'].items()]
        print_table(headers, rows)
        
        # ups.status 기반 판정
        ups_status = ups_data['data'].get('ups.status', 'N/A')
        if 'OL' in ups_status:
            print("")
            print_pass(f"UPS 상태: {ups_status} (정상)")
        elif 'OB' in ups_status:
            print("")
            print_warning(f"UPS 상태: {ups_status} (배터리 모드)")
        else:
            print("")
            print_warning(f"UPS 상태: {ups_status}")
    else:
        print_fail("UPS 데이터 조회 실패")
        print(f"  오류: {ups_data.get('error', 'Unknown error')}")
        result['error'] = ups_data.get('error', 'Unknown error')
    
    # 4. 설정 파일 확인
    print("")
    print_info("NUT 설정 파일 확인 중...")
    config_files = check_config_files()
    result['config_files'] = config_files
    
    all_exists = all(config_files.values())
    if all_exists:
        print_pass(f"모든 설정 파일 존재 ({len(config_files)}개)")
    else:
        missing = [f for f, exists in config_files.items() if not exists]
        print_warning(f"일부 설정 파일 누락: {', '.join(missing)}")
    
    # NAS 연결 확인은 NAS 점검 항목에서 수행되므로 여기서는 제외
    
    # 전체 상태 판정
    print("")
    
    # 각 항목별 상태 확인
    services_ok = services['all_active']
    port_ok = port['listening']
    ups_ok = ups_data['success']
    
    # NAS 연결 확인은 선택적 체크 (FAIL 판정에서 제외)
    # NAS가 원격 NUT 클라이언트로 연결된 경우 로그에 항상 기록되는 것은 아님
    
    if services_ok and port_ok and ups_ok:
        result['status'] = 'PASS'
        print_pass("UPS/NUT 점검 결과: PASS")
    else:
        result['status'] = 'FAIL'
        print_fail("UPS/NUT 점검 결과: FAIL")
        
        # 실패 원인 표시
        failures = []
        if not services_ok:
            failures.append("서비스 비활성")
        if not port_ok:
            failures.append("포트 미리스닝")
        if not ups_ok:
            failures.append("UPS 데이터 조회 실패")
        
        print(f"  실패 원인: {', '.join(failures)}")
    
    return result

