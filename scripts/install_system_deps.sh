#!/usr/bin/env bash
# Installs Android toolchain dependencies for the APK signer bot.
# Run once on a fresh VM (not part of the automatic update script).
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  SUDO=sudo
else
  SUDO=
fi

echo "==> Installing apt packages"
$SUDO DEBIAN_FRONTEND=noninteractive apt-get update -qq
$SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  openjdk-17-jdk wget unzip curl p7zip-full

echo "==> Installing apktool 2.9.3"
$SUDO wget -q https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool
$SUDO chmod +x /usr/local/bin/apktool
$SUDO wget -q https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O /usr/local/bin/apktool.jar
$SUDO chmod +x /usr/local/bin/apktool.jar

echo "==> Installing zipalign (Android build-tools 34)"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
wget -q -O "$TMP/build-tools.zip" https://dl.google.com/android/repository/build-tools_r34-linux.zip
$SUDO unzip -q "$TMP/build-tools.zip" -d /opt/android
$SUDO mv /opt/android/android-14 /opt/android/build-tools
$SUDO ln -sf /opt/android/build-tools/zipalign /usr/local/bin/zipalign

echo "==> Installing AndResGuard CLI JAR"
# The Dockerfile URL (1.2.21) returns 404; use the prebuilt JAR from the upstream repo.
ANDRES_SRC=$(mktemp -d)
git clone --depth 1 https://github.com/shwenzhang/AndResGuard.git "$ANDRES_SRC"
$SUDO cp "$ANDRES_SRC/tool_output/AndResGuard-cli-1.2.15.jar" /opt/AndResGuard.jar
$SUDO chmod 644 /opt/AndResGuard.jar
rm -rf "$ANDRES_SRC"

echo "==> Verifying toolchain"
java -version
apktool --version
zipalign 2>&1 | head -1
java -jar /opt/AndResGuard.jar -h 2>&1 | head -1
echo "==> System dependencies installed successfully"
