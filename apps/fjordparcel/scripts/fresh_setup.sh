#!/usr/bin/env sh
# Alias for fresh_setup_lxc.sh — same script, shorter name.
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec sh "${SCRIPT_DIR}/fresh_setup_lxc.sh" "$@"
