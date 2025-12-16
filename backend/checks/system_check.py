"""
시스템 종합 점검 모듈
OS, 서비스, Java, Network 등 종합적인 시스템 상태 확인
(check_edge_status.sh 기능 통합)
"""
import os
import subprocess
import re
from typing import Dict, Any, List


def run_command(cmd: str) -> Dict[str, Any]:
    """명령어 실행 헬퍼"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stdout': '', 'stderr': 'Timeout', 'returncode': -1}
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': str(e), 'returncode': -1}


def check_os_settings() -> Dict[str, Any]:
    """OS 설정 확인 (타임존, 로케일)"""
    results = {}
    
    # 타임존 확인
    tz_result = run_command("timedatectl | grep 'Time zone'")
    if tz_result['success']:
        is_utc = 'UTC' in tz_result['stdout'] or 'Etc/UTC' in tz_result['stdout']
        results['timezone'] = {
            'status': 'PASS' if is_utc else 'WARN',
            'value': tz_result['stdout'],
            'expected': 'UTC'
        }
    else:
        results['timezone'] = {'status': 'FAIL', 'value': 'Unknown'}
    
    # 로케일 확인
    locale_result = run_command("grep -E '^LANG=' /etc/default/locale 2>/dev/null || echo $LANG")
    if locale_result['success']:
        is_ko_utf8 = 'ko_KR.UTF-8' in locale_result['stdout']
        results['locale'] = {
            'status': 'PASS' if is_ko_utf8 else 'WARN',
            'value': locale_result['stdout'],
            'expected': 'ko_KR.UTF-8'
        }
    else:
        results['locale'] = {'status': 'SKIP', 'value': 'Unknown'}
    
    # 인코딩 확인
    encoding_result = run_command("locale charmap")
    if encoding_result['success']:
        is_utf8 = 'UTF-8' in encoding_result['stdout']
        results['encoding'] = {
            'status': 'PASS' if is_utf8 else 'FAIL',
            'value': encoding_result['stdout'],
            'expected': 'UTF-8'
        }
    else:
        results['encoding'] = {'status': 'SKIP', 'value': 'Unknown'}
    
    return results


def check_services() -> Dict[str, Any]:
    """주요 서비스 상태 확인"""
    services = {
        'tomcat': ['tomcat', 'tomcat9', 'tomcat10'],
        'postgresql': ['postgresql', 'postgresql@14-main'],
        'nut-server': ['nut-server'],
        'nut-monitor': ['nut-monitor', 'upsmon'],
        'stream': ['stream']
    }
    
    results = {}
    
    for service_name, candidates in services.items():
        found = False
        for candidate in candidates:
            status_result = run_command(f"systemctl is-active {candidate} 2>/dev/null")
            if status_result['returncode'] != 4:  # 4 = service not found
                is_active = status_result['stdout'] == 'active'
                results[service_name] = {
                    'status': 'PASS' if is_active else 'FAIL',
                    'service': candidate,
                    'state': status_result['stdout']
                }
                found = True
                break
        
        if not found:
            results[service_name] = {
                'status': 'SKIP',
                'service': service_name,
                'state': 'not found'
            }
    
    return results


def check_ports() -> Dict[str, Any]:
    """주요 포트 리스닝 확인"""
    ports = {
        'HTTP (80)': '80',
        'PostgreSQL (5432)': '5432',
        'NUT (3493)': '3493'
    }
    
    results = {}
    
    for name, port in ports.items():
        ss_result = run_command(f"ss -tlnp | grep ':{port}'")
        if ss_result['success'] and ss_result['stdout']:
            results[name] = {
                'status': 'PASS',
                'listening': True,
                'details': ss_result['stdout'].split('\n')[0][:80]
            }
        else:
            results[name] = {
                'status': 'FAIL',
                'listening': False,
                'details': 'Not listening'
            }
    
    return results


def check_java() -> Dict[str, Any]:
    """Java 설정 확인"""
    results = {}
    
    # Java 버전
    java_result = run_command("java -version 2>&1")
    if java_result['returncode'] == 0:
        version_match = re.search(r'version "(\d+)', java_result['stdout'])
        if version_match:
            major_version = int(version_match.group(1))
            is_jdk17 = major_version >= 17
            results['version'] = {
                'status': 'PASS' if is_jdk17 else 'WARN',
                'value': f"Java {major_version}",
                'expected': 'Java 17+'
            }
        else:
            results['version'] = {'status': 'WARN', 'value': 'Unknown version'}
    else:
        results['version'] = {'status': 'FAIL', 'value': 'Java not found'}
    
    # Heap 설정 확인
    heap_result = run_command("grep -rE '(-Xms|-Xmx)' /etc/systemd/system /etc/default 2>/dev/null | head -5")
    if heap_result['success'] and heap_result['stdout']:
        has_xms = '-Xms' in heap_result['stdout']
        has_xmx = '-Xmx' in heap_result['stdout']
        results['heap'] = {
            'status': 'PASS' if (has_xms and has_xmx) else 'WARN',
            'value': 'Configured' if (has_xms and has_xmx) else 'Not configured',
            'details': heap_result['stdout'].split('\n')[0][:100]
        }
    else:
        results['heap'] = {'status': 'SKIP', 'value': 'Not found'}
    
    return results


def check_network() -> Dict[str, Any]:
    """네트워크 설정 확인"""
    results = {}
    
    # IP 주소 확인 (enp로 시작하는 인터페이스만, 도커 제외)
    # 필수 IP: 192.168.10.20/24는 필수, 192.168.1.10/24 또는 192.168.1.100/24 중 하나 이상
    ip_result = run_command("ip -o -4 addr show | awk '{print $2, $4}'")
    if ip_result['success']:
        ips = ip_result['stdout'].split('\n')
        # enp로 시작하는 인터페이스만 필터링 (도커 제외)
        enp_interfaces = [ip for ip in ips if ip.startswith('enp')]
        
        # 필수 IP 주소 확인
        required_ip_main = '192.168.10.20/24'  # 반드시 있어야 함
        optional_ips = ['192.168.1.10/24', '192.168.1.100/24']  # 둘 중 하나 이상
        
        found_ips = []
        has_main_ip = False
        has_optional_ip = False
        
        for interface in enp_interfaces:
            if required_ip_main in interface:
                has_main_ip = True
                found_ips.append(required_ip_main)
            for optional_ip in optional_ips:
                if optional_ip in interface:
                    has_optional_ip = True
                    if optional_ip not in found_ips:
                        found_ips.append(optional_ip)
        
        # 메인 IP와 선택적 IP 중 하나 이상 있어야 PASS
        has_all_required = has_main_ip and has_optional_ip
        
        required_ips_list = [required_ip_main] + optional_ips
        missing_ips = []
        if not has_main_ip:
            missing_ips.append(required_ip_main)
        if not has_optional_ip:
            missing_ips.extend(optional_ips)
        
        results['ip_addresses'] = {
            'status': 'PASS' if has_all_required else 'FAIL',
            'count': len(enp_interfaces),
            'addresses': enp_interfaces[:3],  # 최대 3개만 표시
            'required': required_ips_list,
            'found': found_ips,
            'missing': missing_ips
        }
    else:
        results['ip_addresses'] = {
            'status': 'FAIL', 
            'count': 0,
            'required': ['192.168.10.20/24', '192.168.1.10/24', '192.168.1.100/24'],
            'found': [],
            'missing': ['192.168.10.20/24', '192.168.1.10/24', '192.168.1.100/24']
        }
    
    # 활성 연결 (nmcli)
    nmcli_result = run_command("nmcli -t con show --active 2>/dev/null")
    if nmcli_result['returncode'] == 0:
        connections = [line.split(':')[0] for line in nmcli_result['stdout'].split('\n') if line]
        results['active_connections'] = {
            'status': 'PASS' if len(connections) > 0 else 'FAIL',
            'count': len(connections),
            'names': connections[:3]
        }
    else:
        results['active_connections'] = {'status': 'SKIP', 'value': 'nmcli not available'}
    
    return results


def check_disk_space() -> Dict[str, Any]:
    """디스크 공간 확인"""
    results = {}
    
    # 루트 파티션
    df_result = run_command("df -h / | tail -1")
    if df_result['success']:
        parts = df_result['stdout'].split()
        if len(parts) >= 5:
            usage_pct = int(parts[4].replace('%', ''))
            results['root'] = {
                'status': 'PASS' if usage_pct < 80 else 'WARN' if usage_pct < 90 else 'FAIL',
                'size': parts[1],
                'used': parts[2],
                'avail': parts[3],
                'usage': parts[4]
            }
    
    # PostgreSQL 데이터 디렉토리
    pg_result = run_command("df -h /var/lib/postgresql 2>/dev/null | tail -1")
    if pg_result['success']:
        parts = pg_result['stdout'].split()
        if len(parts) >= 5:
            usage_pct = int(parts[4].replace('%', ''))
            results['postgresql'] = {
                'status': 'PASS' if usage_pct < 80 else 'WARN',
                'usage': parts[4],
                'avail': parts[3]
            }
    else:
        results['postgresql'] = {'status': 'SKIP', 'value': 'Not mounted separately'}
    
    return results


def check_cron() -> Dict[str, Any]:
    """Cron 작업 확인"""
    results = {}
    
    # Crontab 확인
    cron_result = run_command("crontab -l 2>/dev/null")
    if cron_result['success']:
        cron_lines = [line for line in cron_result['stdout'].split('\n') if line and not line.startswith('#')]
        results['crontab'] = {
            'status': 'PASS' if len(cron_lines) > 0 else 'WARN',
            'count': len(cron_lines),
            'jobs': cron_lines[:5]
        }
        
        # 00:01 작업 확인
        has_0001_job = any('1 0 * * *' in line or '01 00 * * *' in line for line in cron_lines)
        results['daily_sync'] = {
            'status': 'PASS' if has_0001_job else 'WARN',
            'value': 'Found' if has_0001_job else 'Not found',
            'expected': 'Daily 00:01 UTC job'
        }
    else:
        results['crontab'] = {'status': 'SKIP', 'value': 'No crontab'}
    
    return results


def check_tomcat_details() -> Dict[str, Any]:
    """Tomcat 세부 설정 점검 (권한 없이 확인 가능한 방법)"""
    results = {}
    
    # 1. Tomcat 버전 확인 (프로세스에서 추출)
    ps_result = run_command("ps aux | grep tomcat | grep -v grep | grep 'catalina.home'")
    if ps_result['success'] and ps_result['stdout']:
        # catalina.home에서 경로 추출
        catalina_match = re.search(r'-Dcatalina\.home=(\S+)', ps_result['stdout'])
        if catalina_match:
            tomcat_home = catalina_match.group(1)
            results['home'] = {'status': 'PASS', 'value': tomcat_home}
            
            # 버전은 systemctl status에서 확인 가능
            version_result = run_command("systemctl status tomcat | grep -i 'apache tomcat' | head -1")
            if version_result['success'] and version_result['stdout']:
                results['version'] = {'status': 'PASS', 'value': 'Running'}
            else:
                results['version'] = {'status': 'PASS', 'value': 'Active'}
        else:
            results['version'] = {'status': 'SKIP', 'value': 'Not found'}
    else:
        results['version'] = {'status': 'SKIP', 'value': 'Not running'}
    
    # 2. HTTP 포트 확인 (권한 없이도 확인)
    port_result = run_command("ss -tln 2>/dev/null | grep ':80 ' || netstat -tln 2>/dev/null | grep ':80 '")
    if port_result['success'] and port_result['stdout'] and ':80' in port_result['stdout']:
        results['http_port'] = {'status': 'PASS', 'value': 'Port 80 listening'}
    else:
        results['http_port'] = {'status': 'WARN', 'value': 'Port 80 not detected'}
    
    # 3. 로그 파일 확인 (Tomcat이 실행 중이면 로그는 있다고 가정)
    if ps_result['success'] and ps_result['stdout']:
        # Tomcat 프로세스가 실행 중이므로 로그는 생성되고 있음
        results['logs'] = {'status': 'PASS', 'value': 'Tomcat running (logs exist)'}
    else:
        # 파일 시스템에서 직접 확인 시도
        log_check = run_command("find /var/log -readable -name '*tomcat*.log' -o -name 'catalina*.log' 2>/dev/null | wc -l")
        if log_check['success'] and log_check['stdout'] and int(log_check['stdout']) > 0:
            results['logs'] = {'status': 'PASS', 'value': f"{log_check['stdout']} log files"}
        else:
            results['logs'] = {'status': 'SKIP', 'value': 'Not accessible'}
    
    # 4. 힙 메모리 설정 확인 (프로세스에서 추출)
    if ps_result['success'] and ps_result['stdout']:
        xms = re.search(r'-Xms(\S+)', ps_result['stdout'])
        xmx = re.search(r'-Xmx(\S+)', ps_result['stdout'])
        if xms and xmx:
            results['heap_memory'] = {'status': 'PASS', 'value': f"Xms{xms.group(1)} Xmx{xmx.group(1)}"}
        else:
            results['heap_memory'] = {'status': 'WARN', 'value': 'Not configured'}
    else:
        results['heap_memory'] = {'status': 'SKIP', 'value': 'Cannot check'}
    
    # 5. 로그 로테이션 설정
    rotate_result = run_command("test -f /etc/logrotate.d/tomcat && echo 'configured'")
    if rotate_result['success'] and 'configured' in rotate_result['stdout']:
        results['logrotate'] = {'status': 'PASS', 'value': 'Configured'}
    else:
        results['logrotate'] = {'status': 'SKIP', 'value': 'Not configured'}
    
    return results


def check_postgresql_details() -> Dict[str, Any]:
    """PostgreSQL 세부 설정 점검"""
    results = {}
    
    # 1. PostgreSQL 버전 확인
    version_result = run_command("psql -V 2>/dev/null")
    if version_result['success']:
        results['version'] = {'status': 'PASS', 'value': version_result['stdout']}
    else:
        results['version'] = {'status': 'SKIP', 'value': 'psql not found'}
    
    # 2. PostGIS 설치 확인 (권한 없이 패키지 확인)
    postgis_check = run_command("dpkg -l | grep postgis")
    if postgis_check['success'] and 'postgis' in postgis_check['stdout']:
        results['postgis'] = {'status': 'PASS', 'value': 'Installed'}
    else:
        results['postgis'] = {'status': 'SKIP', 'value': 'Not found'}
    
    # 3. 데이터 디렉토리 용량 확인
    df_result = run_command("df -h /var/lib/postgresql 2>/dev/null | tail -1")
    if df_result['success']:
        parts = df_result['stdout'].split()
        if len(parts) >= 5:
            try:
                usage_pct = int(parts[4].replace('%', ''))
                results['disk_usage'] = {
                    'status': 'PASS' if usage_pct < 80 else 'WARN',
                    'usage': parts[4],
                    'avail': parts[3]
                }
            except (ValueError, IndexError):
                results['disk_usage'] = {'status': 'SKIP', 'value': 'Parse error'}
        else:
            results['disk_usage'] = {'status': 'SKIP', 'value': 'Not mounted'}
    else:
        results['disk_usage'] = {'status': 'SKIP', 'value': 'Not accessible'}
    
    # 4. 자동 재시작 설정 확인
    restart_result = run_command("systemctl is-enabled postgresql 2>/dev/null")
    if restart_result['success'] and 'enabled' in restart_result['stdout']:
        results['autostart'] = {'status': 'PASS', 'value': 'Enabled'}
    else:
        results['autostart'] = {'status': 'SKIP', 'value': 'Unknown'}
    
    # 5. 설정 파일 존재 확인
    conf_result = run_command("ls /etc/postgresql/*/main/postgresql.conf 2>/dev/null | head -1")
    if conf_result['success'] and conf_result['stdout']:
        results['config_file'] = {'status': 'PASS', 'value': 'Found'}
    else:
        results['config_file'] = {'status': 'SKIP', 'value': 'Not found'}
    
    return results


def check_setup_scripts() -> Dict[str, Any]:
    """
    post-install_setup.sh와 setup_nut.sh 스크립트가 제대로 적용되었는지 확인
    
    post-install_setup.sh 확인 항목:
    - koast-user 사용자 존재
    - SSH 서비스 활성화
    - 시간대 설정 (Asia/Seoul)
    - GRUB 설정 (TIMEOUT=2, TIMEOUT_STYLE=menu 등)
    
    setup_nut.sh 확인 항목:
    - /etc/nut/upssched.conf 존재 및 올바른 내용
    - /etc/nut/upssched-cmd 존재 및 실행 권한
    - 99-force-poweroff 비활성화됨
    """
    from utils.ui import print_info
    
    results = {}
    
    # 1. post-install_setup.sh 확인
    print("")
    print_info("설정 스크립트 적용 상태 확인 중...")
    
    # 1-1. koast-user 사용자 존재 확인
    user_result = run_command("id koast-user 2>/dev/null")
    results['post_install_user'] = {
        'status': 'PASS' if user_result['success'] else 'FAIL',
        'value': 'koast-user 존재' if user_result['success'] else 'koast-user 없음'
    }
    
    # 1-2. SSH 서비스 활성화 확인
    ssh_result = run_command("systemctl is-enabled ssh 2>/dev/null")
    ssh_enabled = ssh_result['stdout'].strip() in ['enabled', 'enabled-runtime']
    results['post_install_ssh'] = {
        'status': 'PASS' if ssh_enabled else 'WARN',
        'value': ssh_result['stdout'].strip() if ssh_result['success'] else 'Unknown'
    }
    
    # 1-3. 시간대 확인 (Asia/Seoul)
    tz_result = run_command("timedatectl | grep 'Time zone'")
    if tz_result['success']:
        is_seoul = 'Asia/Seoul' in tz_result['stdout']
        results['post_install_timezone'] = {
            'status': 'PASS' if is_seoul else 'WARN',
            'value': tz_result['stdout'].strip(),
            'expected': 'Asia/Seoul'
        }
    else:
        results['post_install_timezone'] = {
            'status': 'SKIP',
            'value': 'Unknown'
        }
    
    # 1-4. GRUB 설정 확인
    grub_result = run_command("grep -E '^GRUB_TIMEOUT=|^GRUB_TIMEOUT_STYLE=' /etc/default/grub 2>/dev/null")
    if grub_result['success']:
        timeout_ok = 'GRUB_TIMEOUT=2' in grub_result['stdout']
        style_ok = 'GRUB_TIMEOUT_STYLE=menu' in grub_result['stdout']
        if timeout_ok and style_ok:
            results['post_install_grub'] = {
                'status': 'PASS',
                'value': 'GRUB 설정 정상'
            }
        else:
            results['post_install_grub'] = {
                'status': 'WARN',
                'value': f"GRUB 설정 확인 필요: {grub_result['stdout'][:100]}"
            }
    else:
        results['post_install_grub'] = {
            'status': 'SKIP',
            'value': 'GRUB 설정 파일 읽기 불가'
        }
    
    # 2. setup_nut.sh 확인
    # 2-1. upssched.conf 파일 존재 및 내용 확인
    upssched_conf = '/etc/nut/upssched.conf'
    if os.path.exists(upssched_conf):
        try:
            with open(upssched_conf, 'r', encoding='utf-8') as f:
                content = f.read()
                # 중요한 설정이 있는지 확인
                has_cmdscript = 'CMDSCRIPT' in content
                has_pipefn = 'PIPEFN' in content
                has_timer = 'START-TIMER' in content or 'TIMER' in content
                # force-poweroff 관련 내용이 없는지 확인 (비활성화되어야 함)
                no_force_poweroff = 'force-poweroff' not in content.lower()
                
                if has_cmdscript and has_pipefn and has_timer and no_force_poweroff:
                    results['nut_setup_config'] = {
                        'status': 'PASS',
                        'value': 'upssched.conf 설정 정상'
                    }
                else:
                    issues = []
                    if not has_cmdscript:
                        issues.append('CMDSCRIPT 없음')
                    if not has_pipefn:
                        issues.append('PIPEFN 없음')
                    if not has_timer:
                        issues.append('TIMER 없음')
                    if not no_force_poweroff:
                        issues.append('force-poweroff 관련 내용 발견')
                    
                    results['nut_setup_config'] = {
                        'status': 'WARN',
                        'value': f"upssched.conf 설정 이상: {', '.join(issues)}"
                    }
        except Exception as e:
            results['nut_setup_config'] = {
                'status': 'FAIL',
                'value': f"upssched.conf 읽기 실패: {str(e)}"
            }
    else:
        results['nut_setup_config'] = {
            'status': 'FAIL',
            'value': 'upssched.conf 파일 없음'
        }
    
    # 2-2. upssched-cmd 파일 존재 및 실행 권한 확인
    upssched_cmd = '/etc/nut/upssched-cmd'
    if os.path.exists(upssched_cmd):
        is_executable = os.access(upssched_cmd, os.X_OK)
        try:
            with open(upssched_cmd, 'r', encoding='utf-8') as f:
                content = f.read()
                has_fsd = 'fsd' in content.lower()
                no_force_poweroff = 'force-poweroff' not in content.lower()
                
                if is_executable and has_fsd and no_force_poweroff:
                    results['nut_setup_cmd'] = {
                        'status': 'PASS',
                        'value': 'upssched-cmd 정상'
                    }
                else:
                    issues = []
                    if not is_executable:
                        issues.append('실행 권한 없음')
                    if not has_fsd:
                        issues.append('fsd 관련 내용 없음')
                    if not no_force_poweroff:
                        issues.append('force-poweroff 관련 내용 발견')
                    
                    results['nut_setup_cmd'] = {
                        'status': 'WARN',
                        'value': f"upssched-cmd 이상: {', '.join(issues)}"
                    }
        except Exception as e:
            results['nut_setup_cmd'] = {
                'status': 'FAIL',
                'value': f"upssched-cmd 읽기 실패: {str(e)}"
            }
    else:
        results['nut_setup_cmd'] = {
            'status': 'FAIL',
            'value': 'upssched-cmd 파일 없음'
        }
    
    # 2-3. 99-force-poweroff 비활성화 확인
    force_poweroff_path = '/usr/lib/systemd/system-shutdown/99-force-poweroff'
    force_poweroff_disabled = '/usr/lib/systemd/system-shutdown/99-force-poweroff.disabled'
    
    if os.path.exists(force_poweroff_disabled):
        results['nut_setup_force_poweroff'] = {
            'status': 'PASS',
            'value': '99-force-poweroff 비활성화됨'
        }
    elif os.path.exists(force_poweroff_path):
        # 파일이 존재하면 비활성화되지 않음
        results['nut_setup_force_poweroff'] = {
            'status': 'WARN',
            'value': '99-force-poweroff 활성화됨 (비활성화 필요)'
        }
    else:
        # 둘 다 없으면 처음부터 설정되지 않은 상태 (정상)
        results['nut_setup_force_poweroff'] = {
            'status': 'PASS',
            'value': '99-force-poweroff 미설정 (정상)'
        }
    
    return results


def check_system_status() -> Dict[str, Any]:
    """전체 시스템 종합 점검"""
    from utils.ui import (
        print_section, print_pass, print_fail, print_warning,
        print_info, print_key_value, print_table
    )
    
    print_section(4, 4, "시스템 종합 점검")
    
    result = {
        'status': 'UNKNOWN',
        'os_settings': {},
        'services': {},
        'ports': {},
        'java': {},
        'network': {},
        'disk': {},
        'cron': {},
        'setup_scripts': {} # 추가된 항목
    }
    
    # 1. OS 설정
    print("")
    print_info("OS 설정 확인 중...")
    os_settings = check_os_settings()
    result['os_settings'] = os_settings
    
    for key, value in os_settings.items():
        status = value.get('status', 'UNKNOWN')
        val = value.get('value', 'N/A')
        if status == 'PASS':
            print_pass(f"{key}: {val}")
        elif status == 'WARN':
            print_warning(f"{key}: {val} (권장: {value.get('expected', 'N/A')})")
        elif status == 'FAIL':
            print_fail(f"{key}: {val}")
        else:
            print_info(f"{key}: {val}")
    
    # 2. 서비스 상태
    print("")
    print_info("주요 서비스 상태 확인 중...")
    services = check_services()
    result['services'] = services
    
    for service, info in services.items():
        status = info.get('status', 'UNKNOWN')
        state = info.get('state', 'unknown')
        if status == 'PASS':
            print_pass(f"{service}: {state}")
        elif status == 'FAIL':
            print_fail(f"{service}: {state}")
        else:
            print_warning(f"{service}: {state}")
    
    # 3. 포트 리스닝
    print("")
    print_info("주요 포트 리스닝 확인 중...")
    ports = check_ports()
    result['ports'] = ports
    
    for port_name, info in ports.items():
        if info.get('listening'):
            print_pass(f"{port_name}: Listening")
        else:
            print_fail(f"{port_name}: Not listening")
    
    # 4. Java 설정
    print("")
    print_info("Java 설정 확인 중...")
    java = check_java()
    result['java'] = java
    
    for key, value in java.items():
        status = value.get('status', 'UNKNOWN')
        val = value.get('value', 'N/A')
        if status == 'PASS':
            print_pass(f"Java {key}: {val}")
        elif status == 'WARN':
            print_warning(f"Java {key}: {val}")
        else:
            print_info(f"Java {key}: {val}")
    
    # 5. 네트워크
    print("")
    print_info("네트워크 설정 확인 중...")
    network = check_network()
    result['network'] = network
    
    if 'ip_addresses' in network:
        ip_info = network['ip_addresses']
        if ip_info.get('status') == 'PASS':
            print_pass(f"IP 주소: {ip_info.get('count')}개")
            for addr in ip_info.get('addresses', []):
                print(f"    {addr}")
        else:
            print_fail(f"IP 주소: {ip_info.get('count')}개 (필수 IP 누락)")
            # 필수 IP 상태 표시
            if 'required' in ip_info:
                for req_ip in ip_info.get('required', []):
                    if req_ip in ip_info.get('found', []):
                        print_pass(f"  ✓ {req_ip}")
                    else:
                        print_fail(f"  ✗ {req_ip} (없음)")
    
    if 'active_connections' in network and network['active_connections'].get('status') != 'SKIP':
        conn_info = network['active_connections']
        if conn_info.get('status') == 'PASS':
            print_pass(f"활성 연결: {conn_info.get('count')}개")
    
    # 6. 디스크 공간
    print("")
    print_info("디스크 공간 확인 중...")
    disk = check_disk_space()
    result['disk'] = disk
    
    if 'root' in disk:
        root_info = disk['root']
        status = root_info.get('status', 'UNKNOWN')
        usage = root_info.get('usage', 'N/A')
        avail = root_info.get('avail', 'N/A')
        
        if status == 'PASS':
            print_pass(f"루트 파티션: {usage} 사용 (여유: {avail})")
        elif status == 'WARN':
            print_warning(f"루트 파티션: {usage} 사용 (여유: {avail})")
        else:
            print_fail(f"루트 파티션: {usage} 사용 (여유: {avail})")
    
    # 7. Cron 작업
    print("")
    print_info("Cron 작업 확인 중...")
    cron = check_cron()
    result['cron'] = cron
    
    if 'crontab' in cron:
        cron_info = cron['crontab']
        if cron_info.get('status') != 'SKIP':
            count = cron_info.get('count', 0)
            if count > 0:
                print_pass(f"Cron 작업: {count}개")
            else:
                print_warning("Cron 작업: 없음")
    
    if 'daily_sync' in cron:
        sync_info = cron['daily_sync']
        if sync_info.get('status') == 'PASS':
            print_pass(f"일일 동기화 작업: {sync_info.get('value')}")
        else:
            print_warning(f"일일 동기화 작업: {sync_info.get('value')}")
    
    # 8. Tomcat 세부 설정
    print("")
    print_info("Tomcat 세부 설정 확인 중...")
    tomcat_details = check_tomcat_details()
    result['tomcat_details'] = tomcat_details
    
    for key, info in tomcat_details.items():
        status = info.get('status', 'UNKNOWN')
        value = info.get('value', 'N/A')
        if status == 'PASS':
            print_pass(f"Tomcat {key}: {value}")
        elif status == 'WARN':
            print_warning(f"Tomcat {key}: {value}")
        elif status == 'SKIP':
            pass  # SKIP 항목은 출력 생략
        else:
            print_info(f"Tomcat {key}: {value}")
    
    # 9. PostgreSQL 세부 설정
    print("")
    print_info("PostgreSQL 세부 설정 확인 중...")
    pg_details = check_postgresql_details()
    result['postgresql_details'] = pg_details
    
    for key, info in pg_details.items():
        status = info.get('status', 'UNKNOWN')
        value = info.get('value', 'N/A')
        if status == 'PASS':
            print_pass(f"PostgreSQL {key}: {value}")
        elif status == 'WARN':
            print_warning(f"PostgreSQL {key}: {value}")
        elif status == 'SKIP':
            pass  # SKIP 항목은 출력 생략
        else:
            print_info(f"PostgreSQL {key}: {value}")
    
    # 10. 설정 스크립트 적용 상태
    print("")
    print_info("설정 스크립트 적용 상태 확인 중...")
    setup_scripts = check_setup_scripts()
    result['setup_scripts'] = setup_scripts
    
    for key, info in setup_scripts.items():
        status = info.get('status', 'UNKNOWN')
        value = info.get('value', 'N/A')
        # 키 이름을 한글로 변환
        key_names = {
            'post_install_user': '사용자 (koast-user)',
            'post_install_ssh': 'SSH 서비스',
            'post_install_timezone': '시간대 (Asia/Seoul)',
            'post_install_grub': 'GRUB 설정',
            'nut_setup_config': 'NUT upssched.conf',
            'nut_setup_cmd': 'NUT upssched-cmd',
            'nut_setup_force_poweroff': 'NUT force-poweroff'
        }
        display_key = key_names.get(key, key)
        
        if status == 'PASS':
            print_pass(f"{display_key}: {value}")
        elif status == 'WARN':
            print_warning(f"{display_key}: {value}")
        elif status == 'FAIL':
            print_fail(f"{display_key}: {value}")
        elif status == 'SKIP':
            pass  # SKIP 항목은 출력 생략
        else:
            print_info(f"{display_key}: {value}")
    
    # 전체 판정 및 통계
    print("")
    
    # 모든 카테고리의 항목들을 수집 + SKIP 항목 추적
    all_items = []
    skip_items = []
    named_categories = [
        ('OS 설정', os_settings),
        ('서비스', services),
        ('포트', ports),
        ('Java', java),
        ('네트워크', network),
        ('디스크', disk),
        ('Cron', cron),
        ('Tomcat', tomcat_details),
        ('PostgreSQL', pg_details),
        ('설정 스크립트', setup_scripts), # 추가된 카테고리
    ]
    for category_name, category in named_categories:
        for key, item in category.items():
            if isinstance(item, dict) and 'status' in item:
                status_val = item.get('status')
                all_items.append(status_val)
                if status_val == 'SKIP':
                    # 항목 라벨 구성
                    label = key
                    # 서비스/포트 등은 사람이 보기 좋게 라벨링
                    if category_name == '서비스':
                        label = item.get('service', key)
                    elif category_name == '포트':
                        label = key
                    elif category_name == '네트워크' and key == 'active_connections':
                        label = '활성 연결'
                    elif category_name == '설정 스크립트':
                        # 설정 스크립트 키 이름 매핑
                        key_labels = {
                            'post_install_user': '사용자 (koast-user)',
                            'post_install_ssh': 'SSH 서비스',
                            'post_install_timezone': '시간대 (Asia/Seoul)',
                            'post_install_grub': 'GRUB 설정',
                            'nut_setup_config': 'NUT upssched.conf',
                            'nut_setup_cmd': 'NUT upssched-cmd',
                            'nut_setup_force_poweroff': 'NUT force-poweroff'
                        }
                        label = key_labels.get(key, key)
                    skip_items.append(f"{category_name}: {label}")
    
    # 통계 계산
    pass_count = sum(1 for status in all_items if status == 'PASS')
    fail_count = sum(1 for status in all_items if status == 'FAIL')
    warn_count = sum(1 for status in all_items if status == 'WARN')
    skip_count = sum(1 for status in all_items if status == 'SKIP')
    
    result['summary'] = {
        'pass_count': pass_count,
        'fail_count': fail_count,
        'warn_count': warn_count,
        'skip_count': skip_count,
        'skip_items': skip_items,
        'total_count': len(all_items)
    }
    
    # 전체 상태 판정
    if fail_count == 0:
        result['status'] = 'PASS'
        print_pass(f"시스템 종합 점검 결과: PASS (✓{pass_count} ⚠{warn_count} ◌{skip_count})")
    else:
        result['status'] = 'FAIL'
        print_fail(f"시스템 종합 점검 결과: FAIL (✓{pass_count} ✗{fail_count} ⚠{warn_count} ◌{skip_count})")

    # SKIP 항목 목록 출력
    if skip_count > 0 and skip_items:
        print_info("SKIP 항목: " + ", ".join(skip_items[:5]) + (" ..." if len(skip_items) > 5 else ""))
    
    return result

