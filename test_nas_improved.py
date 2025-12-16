#!/usr/bin/env python3
"""
NAS Check 개선 버전 테스트
"""
import os
import sys
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks.nas_check import check_nas_status

def main():
    print("=" * 60)
    print("NAS Check 개선 버전 테스트")
    print("=" * 60)
    print()
    
    # .env에서 설정 읽기
    nas_config = {
        'ip': os.getenv('NAS_IP', '192.168.10.30'),
        'user': os.getenv('NAS_USER', 'admin'),
        'password': os.getenv('NAS_PASSWORD', ''),
        'port': os.getenv('NAS_PORT', '2222')
    }
    
    print(f"📋 NAS 설정:")
    print(f"  IP: {nas_config['ip']}")
    print(f"  User: {nas_config['user']}")
    print(f"  Port: {nas_config['port']}")
    print()
    
    # NAS 체크 실행
    result = check_nas_status(nas_config)
    
    # 결과 요약
    print()
    print("=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"최종 상태: {result['status']}")
    print(f"연결 상태: {result['connection']}")
    
    if result.get('errors'):
        print(f"\n🔴 오류 ({len(result['errors'])}개):")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result.get('warnings'):
        print(f"\n🟡 경고 ({len(result['warnings'])}개):")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    if result['status'] == 'PASS':
        print("\n✅ 모든 검사 정상!")
    
    print()
    print("=" * 60)
    
    # 종료 코드
    if result['status'] == 'FAIL':
        sys.exit(1)
    elif result['status'] == 'WARN':
        sys.exit(0)  # 경고는 성공으로 처리
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()

