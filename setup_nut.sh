#!/usr/bin/env bash
set -euo pipefail

ts() { date +%Y%m%d-%H%M%S; }
bk() { [ -f "$1" ] && cp -a "$1" "${1}.bak.$(ts)" || true; }

echo "[1] 백업"
install -d -m 755 /etc/nut /root
bk /etc/nut/upssched.conf
bk /etc/nut/upssched-cmd
[ -f /usr/lib/systemd/system-shutdown/99-force-poweroff ] && cp -a /usr/lib/systemd/system-shutdown/99-force-poweroff "/usr/lib/systemd/system-shutdown/99-force-poweroff.bak.$(ts)" || true

echo "[2] 문제 구문 제거된 /etc/nut/upssched.conf 재작성"
cat >/etc/nut/upssched.conf <<'EOF'
CMDSCRIPT /etc/nut/upssched-cmd
PIPEFN /var/run/nut/upssched.pipe
LOCKFN /var/run/nut/upssched.lock

# 정전 발생 시 타이머 시작
AT ONBATT * EXECUTE log-onbatt
AT ONBATT * START-TIMER ob120 120

# 타이머 만료 시 FSD 트리거
AT TIMER  ob120 EXECUTE trigger-fsd

# 상전원 복구 시 타이머 취소
AT ONLINE * CANCEL-TIMER ob120
AT ONLINE * EXECUTE log-online
EOF
chmod 0644 /etc/nut/upssched.conf

echo "[3] 문제 분기 제거된 /etc/nut/upssched-cmd 재작성(강제전원차단 호출 삭제)"
cat >/etc/nut/upssched-cmd <<'EOF'
#!/bin/sh
logger -t upssched-cmd "EXECUTE: $1 (user: $(whoami))"

case "$1" in
  trigger-fsd|ob*)
    logger -t upssched-cmd "Timer expired -> upsmon -c fsd"
    /usr/sbin/upsmon -c fsd
    ;;
  log-onbatt)
    logger -t upssched-cmd "ONBATT timer started"
    ;;
  log-online)
    logger -t upssched-cmd "ONLINE timer canceled"
    ;;
  *)
    logger -t upssched-cmd "unknown EXECUTE: $1"
    ;;
esac
EOF
chmod 0755 /etc/nut/upssched-cmd

echo "[4] 99-force-poweroff 비활성화(존재 시)"
if [ -f /usr/lib/systemd/system-shutdown/99-force-poweroff ]; then
  mv -f /usr/lib/systemd/system-shutdown/99-force-poweroff /usr/lib/systemd/system-shutdown/99-force-poweroff.disabled
  chmod 000 /usr/lib/systemd/system-shutdown/99-force-poweroff.disabled || true
fi

echo "[5] 개행/형식 정규화"
command -v dos2unix >/dev/null 2>&1 && dos2unix /etc/nut/upssched.conf /etc/nut/upssched-cmd >/dev/null 2>&1 || true

echo "[6] NUT 재시작"
systemctl stop nut-monitor nut-server 2>/dev/null || true
pkill -9 upssched 2>/dev/null || true
pkill -9 upsmon   2>/dev/null || true
rm -f /var/run/nut/upssched.pipe /var/run/nut/upssched.lock 2>/dev/null || true
systemctl start nut-server
systemctl start nut-monitor

echo "[7] 점검"
grep -n 'force-poweroff' /etc/nut/upssched.conf /etc/nut/upssched-cmd || true
[ -f /usr/lib/systemd/system-shutdown/99-force-poweroff ] && echo "WARNING: 99-force-poweroff still exists" || echo "OK: 99-force-poweroff not present"
systemctl --no-pager status nut-monitor | sed -n '1,15p' || true

echo "완료"
