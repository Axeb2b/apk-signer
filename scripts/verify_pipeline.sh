#!/usr/bin/env bash
# Verifies the APK processing pipeline (same steps as bot.py) without Telegram.
set -euo pipefail

INPUT_APK="${1:-/tmp/test_input.apk}"
WORK_DIR=$(mktemp -d)
OUT_DIR="$WORK_DIR/andres_out"
mkdir -p "$OUT_DIR"

cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

echo "==> Input APK: $INPUT_APK"
test -f "$INPUT_APK"

CONFIG="$WORK_DIR/config.xml"
cat > "$CONFIG" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<resproguard>
  <issue id="property">
    <seventzip value="false"/>
    <metaname value="META-INF"/>
    <keeproot value="false"/>
    <mergeDuplicatedRes value="true"/>
  </issue>
  <issue id="whitelist" isactive="false"/>
  <issue id="compress" isactive="true">
    <path value="*.png"/>
    <path value="*.jpg"/>
    <path value="*.jpeg"/>
    <path value="*.gif"/>
  </issue>
</resproguard>
EOF

echo "==> Step 1: AndResGuard obfuscation"
java -jar /opt/AndResGuard.jar "$INPUT_APK" -config "$CONFIG" -out "$OUT_DIR"

OBF_APK=""
for f in "$OUT_DIR"/*.apk; do
  if [[ "$f" == *unsigned* ]]; then
    OBF_APK="$f"
    break
  fi
done
if [[ -z "$OBF_APK" ]]; then
  echo "ERROR: AndResGuard unsigned APK not found in $OUT_DIR"
  ls -la "$OUT_DIR"
  exit 1
fi
echo "    Obfuscated APK: $OBF_APK ($(du -h "$OBF_APK" | cut -f1))"

echo "==> Step 2: apktool decompile + dummy asset + recompile"
DEC_DIR="$WORK_DIR/dec"
apktool d "$OBF_APK" -o "$DEC_DIR" -f
mkdir -p "$DEC_DIR/assets"
DUMMY="r_$(openssl rand -hex 4).bin"
dd if=/dev/urandom of="$DEC_DIR/assets/$DUMMY" bs=256 count=1 status=none
RECOMPILED="$WORK_DIR/recompiled.apk"
apktool b "$DEC_DIR" -o "$RECOMPILED"
echo "    Recompiled APK: $RECOMPILED ($(du -h "$RECOMPILED" | cut -f1))"

echo "==> Step 3: Random keystore signing + zipalign"
KEYSTORE="$WORK_DIR/random.keystore"
STOREPASS="testpass1234"
keytool -genkey -v -keystore "$KEYSTORE" -alias rnd \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Random, OU=Random, O=Random, L=Random, ST=Random, C=IN" \
  -storepass "$STOREPASS" -keypass "$STOREPASS" -noprompt

jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore "$KEYSTORE" -storepass "$STOREPASS" -keypass "$STOREPASS" \
  "$RECOMPILED" rnd

FINAL="$WORK_DIR/final.apk"
zipalign -v -p 4 "$RECOMPILED" "$FINAL"
echo "    Final APK: $FINAL ($(du -h "$FINAL" | cut -f1))"

OUTPUT="/tmp/randomized_output.apk"
cp "$FINAL" "$OUTPUT"
echo "==> SUCCESS: Pipeline complete. Output saved to $OUTPUT"
