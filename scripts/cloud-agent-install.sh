#!/usr/bin/env bash
# Idempotent Cloud Agent install: Android toolchain + Python deps.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

toolchain_ready() {
  command -v java >/dev/null \
    && command -v apktool >/dev/null \
    && command -v zipalign >/dev/null \
    && test -f /opt/AndResGuard.jar
}

if ! toolchain_ready; then
  echo "==> Installing Android APK toolchain"
  bash "$ROOT/scripts/install_system_deps.sh"
else
  echo "==> Android APK toolchain already installed"
fi

echo "==> Installing Python dependencies"
pip3 install --user -q -r requirements.txt
pip3 install --user -q -r requirements-rag.txt

echo "==> Cloud Agent install complete"
