#!/usr/bin/env bash
# Respected Brain v0.0.1 — Linux & macOS One-Liner Kaldırma Başlatıcı

set -euo pipefail

echo ">> Respected Brain v0.0.1 — Kaldırma Başlatıcı (Uninstaller)"

# 1. Python Tespiti
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "HATA: Python 3 bulunamadı." >&2
    exit 1
fi

# 2. uninstall.py tespiti veya indirme
SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
SCRIPT_DIR=""
if [ -n "${SCRIPT_SOURCE}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_SOURCE}")" 2>/dev/null && pwd)"
fi
UNINSTALL_PY="${SCRIPT_DIR:+${SCRIPT_DIR}/}uninstall.py"

if [ -z "${SCRIPT_DIR}" ] || [ ! -f "${UNINSTALL_PY}" ]; then
    TMP_DIR="$(mktemp -d -t respected-brain-uninstall-XXXXXX)"
    echo "• Kaldırma paketi indiriliyor..."
    if command -v git >/dev/null 2>&1; then
        git clone --depth 1 https://github.com/respected0/respectedbrain.git "${TMP_DIR}" >/dev/null 2>&1
        UNINSTALL_PY="${TMP_DIR}/uninstall.py"
    else
        ZIP_FILE="${TMP_DIR}/repo.zip"
        if command -v curl >/dev/null 2>&1; then
            curl -sSL "https://github.com/respected0/respectedbrain/archive/refs/heads/main.zip" -o "${ZIP_FILE}"
        elif command -v wget >/dev/null 2>&1; then
            wget -q "https://github.com/respected0/respectedbrain/archive/refs/heads/main.zip" -O "${ZIP_FILE}"
        fi
        if command -v unzip >/dev/null 2>&1; then
            unzip -q "${ZIP_FILE}" -d "${TMP_DIR}"
            rm -f "${ZIP_FILE}"
            if [ -d "${TMP_DIR}/respectedbrain-main" ]; then
                UNINSTALL_PY="${TMP_DIR}/respectedbrain-main/uninstall.py"
            else
                UNINSTALL_PY="${TMP_DIR}/uninstall.py"
            fi
        else
            echo "HATA: git veya unzip bulunamadı." >&2
            exit 1
        fi
    fi
    trap 'rm -rf "${TMP_DIR}"' EXIT
fi

# 3. uninstall.py'ı argümanlarla çalıştır
"${PYTHON_BIN}" "${UNINSTALL_PY}" "$@"
