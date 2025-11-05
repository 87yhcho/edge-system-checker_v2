#!/usr/bin/env bash
set -euo pipefail

# === 설정값 ===
NEW_USER="${NEW_USER:-koast-user}"   # 사용자명 변경 가능
NEW_USER_PASSWORD="${NEW_USER_PASSWORD:-koast}" 
SET_TIMEZONE="${SET_TIMEZONE:-Asia/Seoul}"
DPOOL_DEVICE="${DPOOL_DEVICE:-/dev/sda}"   # ZFS 풀용 장치
DPOOL_NAME="${DPOOL_NAME:-dpool}"
ENABLE_DPOOL_CREATE="${ENABLE_DPOOL_CREATE:-no}"  # yes로 해야 실행

log() { printf '[*] %s\n' "$*" >&2; }
err() { printf '[!] %s\n' "$*" >&2; }

require_root() {
  if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
    err "root로 실행하세요: sudo bash post-install_setup.sh"
    exit 1
  fi
}

backup_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  cp -a "$f" "${f}.$(date +%Y%m%d_%H%M%S).bak"
}

install_pkgs() {
  log "패키지 업데이트/업그레이드"
  apt update && apt upgrade -y

  log "OpenSSH 서버, 한글 입력기/언어팩 설치"
  DEBIAN_FRONTEND=noninteractive apt install -y \
    openssh-server ibus-hangul language-pack-ko
}

create_user_and_enable_ssh() {
  if ! id -u "$NEW_USER" >/dev/null 2>&1; then
    log "사용자 생성: ${NEW_USER}"
    adduser --disabled-password --gecos "" "$NEW_USER"
  else
    log "사용자 존재: ${NEW_USER}"
  fi
  usermod -aG sudo "$NEW_USER"

 # 자동 비밀번호 설정
  log "사용자 비밀번호 설정"
  echo "${NEW_USER}:${NEW_USER_PASSWORD}" | chpasswd


  systemctl enable ssh
  systemctl restart ssh
}

set_timezone() {
  if [[ -n "$SET_TIMEZONE" ]]; then
    log "시간대 설정: ${SET_TIMEZONE}"
    timedatectl set-timezone "$SET_TIMEZONE" || true
  fi
}

configure_grub() {
  local f="/etc/default/grub"
  backup_file "$f"

  log "GRUB 설정 수정: $f"
  awk '
    BEGIN {found_timeout=0; found_style=0; found_default=0}
    /^GRUB_TIMEOUT=/      {print "GRUB_TIMEOUT=2"; found_timeout=1; next}
    /^GRUB_TIMEOUT_STYLE=/ {print "GRUB_TIMEOUT_STYLE=menu"; found_style=1; next}
    /^GRUB_CMDLINE_LINUX_DEFAULT=/ {print "GRUB_CMDLINE_LINUX_DEFAULT=\"\""; found_default=1; next}
    {print}
    END {
      if(!found_timeout)      print "GRUB_TIMEOUT=2"
      if(!found_style)        print "GRUB_TIMEOUT_STYLE=menu"
      if(!found_default)      print "GRUB_CMDLINE_LINUX_DEFAULT=\"\""
      print "GRUB_RECORDFAIL_TIMEOUT=2"
    }
  ' "$f" > "$f.new"

  mv "$f.new" "$f"
  log "update-grub 실행"
  update-grub
}

maybe_create_zfs_dpool() {
  if [[ "${ENABLE_DPOOL_CREATE}" != "yes" ]]; then
    log "ZFS 데이터풀 생성: 비활성화(ENABLE_DPOOL_CREATE=yes 로 명시해야 실행)"
    return 0
  fi
  if [[ ! -b "$DPOOL_DEVICE" ]]; then
    err "장치가 블록 디바이스가 아님: $DPOOL_DEVICE"
    exit 2
  fi
  log "!!! 경고: ${DPOOL_DEVICE} 의 모든 데이터가 삭제됩니다. 10초 대기 후 진행(Ctrl+C 로 취소)."
  sleep 10

  wipefs -a "$DPOOL_DEVICE"
  if ! command -v zpool >/dev/null 2>&1; then
    log "zfsutils-linux 설치"
    apt install -y zfsutils-linux
  fi
  zpool create "$DPOOL_NAME" "$DPOOL_DEVICE"
  zfs set mountpoint="/${DPOOL_NAME}" "${DPOOL_NAME}"
  zpool status
  zfs list
}

main() {
  require_root
  install_pkgs
  create_user_and_enable_ssh
  set_timezone
  configure_grub
  maybe_create_zfs_dpool
  log "완료"
}

main "$@"