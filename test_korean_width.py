#!/usr/bin/env python3
"""한글 문자 너비 계산 테스트"""
from checker import get_display_width, pad_string

print("=== 문자 너비 테스트 ===")
print(f"'카메라' 너비: {get_display_width('카메라')}")
print(f"'IP' 너비: {get_display_width('IP')}")
print(f"'원본' 너비: {get_display_width('원본')}")
print(f"'PASS' 너비: {get_display_width('PASS')}")

print("\n=== 패딩 테스트 ===")
print(f"[{pad_string('카메라', 12)}] <- 12칸")
print(f"[{pad_string('IP', 12)}] <- 12칸")
print(f"[{pad_string('원본', 10)}] <- 10칸")
print(f"[{pad_string('PASS', 10)}] <- 10칸")

print("\n=== 정렬 테스트 ===")
header_camera = pad_string("카메라", 12)
header_ip = pad_string("IP", 17)
header_source = pad_string("원본", 10)
header_blur = pad_string("블러", 10)
header_log = pad_string("로그", 10)
print(f"  {header_camera} {header_ip} {header_source} {header_blur} {header_log}")

name = pad_string("카메라 1", 12)
ip = pad_string("192.168.1.101", 17)
source = pad_string("PASS", 10)
blur = pad_string("PASS", 10)
log = pad_string("PASS", 10)
print(f"  {name} {ip} {source} {blur} {log}")

