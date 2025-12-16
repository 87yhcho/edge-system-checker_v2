#!/usr/bin/env python3
"""
UPS 점검 테스트 스크립트
"""
import os
from dotenv import load_dotenv

load_dotenv()

from checks.ups_check import check_ups_status

if __name__ == '__main__':
    print("UPS 점검 테스트 시작...")
    print("")
    
    ups_name = os.getenv('NUT_UPS_NAME', 'ups')
    nas_ip = os.getenv('NAS_IP', '192.168.10.30')
    
    result = check_ups_status(ups_name=ups_name, nas_ip=nas_ip)
    
    print("")
    print("=" * 80)
    print("테스트 완료!")
    print(f"결과: {result.get('status', 'UNKNOWN')}")
    print("=" * 80)

