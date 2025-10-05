#!/usr/bin/env bash
set -Eeuo pipefail

# read desired ids
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"
APPUSER="${APPUSER:-appuser}"
APPGROUP="${APPGROUP:-appgroup}"

# create group/user if missing
if ! getent group "${APPGROUP}" >/dev/null 2>&1; then
  groupadd -g "${PGID}" "${APPGROUP}"
fi
if ! id -u "${APPUSER}" >/dev/null 2>&1; then
  useradd -u "${PUID}" -g "${APPGROUP}" -m -s /usr/sbin/nologin "${APPUSER}"
fi

# make sure $HOME exists and is owned (skip errors on bind-mounts)
mkdir -p "${HOME:-/data}" || true
chown -R "${PUID}:${PGID}" "${HOME:-/data}" 2>/dev/null || true

# if no command provided, fall back to the image CMD
if [ "$#" -eq 0 ]; then
  set -- python -u /app/main.py
fi

# drop privileges (prefer gosu; fall back to setpriv)
if command -v gosu >/dev/null 2>&1; then
  exec gosu "${PUID}:${PGID}" "$@"
elif command -v setpriv >/dev/null 2>&1; then
  exec setpriv --reuid "${PUID}" --regid "${PGID}" --init-groups -- "$@"
else
  echo "warning: no gosu/setpriv; running as current user" >&2
  exec "$@"
fi
