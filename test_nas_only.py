#!/usr/bin/env python3
"""
NAS Check만 단독 테스트
"""
import os
import sys
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks.nas_check import check_nas_status

def main():
    print("="*60)
    print("NAS Check v2.1 테스트 (포트 Fallback 포함)")
    print("="*60)
    print()
    
    # .env에서 설정 읽기
    nas_config = {
        'ip': os.getenv('NAS_IP', '192.168.10.30'),
        'user': os.getenv('NAS_USER', 'admin'),
        'password': os.getenv('NAS_PASSWORD', ''),
        'port': os.getenv('NAS_PORT', '2222')
    }
    
    print(f"설정 정보:")
    print(f"  IP: {nas_config['ip']}")
    print(f"  User: {nas_config['user']}")
    print(f"  Port: {nas_config['port']} (실패 시 22로 재시도)")
    print()
    
    # NAS 체크 실행
    result = check_nas_status(nas_config)
    
    # 결과 요약
    print()
    print("="*60)
    print("테스트 결과")
    print("="*60)
    print(f"상태: {result['status']}")
    print(f"연결: {result['connection']}")
    if result.get('connected_port'):
        print(f"연결 포트: {result['connected_port']}")
    
    if result.get('errors'):
        print(f"\n오류 ({len(result['errors'])}개):")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result.get('warnings'):
        print(f"\n경고 ({len(result['warnings'])}개):")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    print()

if __name__ == '__main__':
    main()

