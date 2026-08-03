# APK Signer Bot

This Telegram bot processes Android APK files sent by users.

## Pipeline

1. **AndResGuard** — obfuscates APK resources (drawables, layouts, etc.)
2. **apktool** — decompiles the APK, injects a random dummy asset file, then recompiles
3. **Signing** — generates a random keystore and signs the APK with `jarsigner`
4. **zipalign** — optimizes APK alignment for Android installation

## Usage

Send an `.apk` file to the bot on Telegram. It replies with a processed `randomized_*.apk`.

## Requirements

- `BOT_TOKEN` — Telegram bot token from BotFather
- Java 17+, apktool, AndResGuard JAR, zipalign
- Python 3 with `python-telegram-bot`

## Commands

- `/start` — welcome message

## Environment

The bot runs in polling mode (no web server). All processing happens locally in a temp directory and is cleaned up after each request.

## Known issues

- AndResGuard 1.2.21 JAR URL in Dockerfile is broken (404)
- Whitelist paths in bot config need full package names for older AndResGuard versions
