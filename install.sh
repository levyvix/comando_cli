#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_PATH="${SCRIPT_DIR}/install-cli.py"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "Python not found. Install Python 3.12+ and try again." >&2
  exit 1
fi

cleanup() {
  if [[ -n "${TMP_DIR:-}" && -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR}"
  fi
}
trap cleanup EXIT

if [[ ! -f "${INSTALLER_PATH}" ]]; then
  RAW_BASE="${COMANDO_CLI_RAW_BASE:-https://raw.githubusercontent.com/levyvix/comando_cli/master}"
  INSTALLER_URL="${RAW_BASE}/install-cli.py"
  TMP_DIR="$(mktemp -d)"
  INSTALLER_PATH="${TMP_DIR}/install-cli.py"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${INSTALLER_URL}" -o "${INSTALLER_PATH}"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "${INSTALLER_PATH}" "${INSTALLER_URL}"
  else
    echo "Neither curl nor wget found. Install one of them and try again." >&2
    exit 1
  fi
fi

exec "${PYTHON_CMD}" "${INSTALLER_PATH}" "$@"
