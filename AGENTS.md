# AGENTS.md

## Project overview

Telegram bot (`bot.py`) that processes APK files: AndResGuard obfuscation → apktool decompile/recompile with dummy asset → random signing → zipalign → reply via Telegram.

## Cursor Cloud specific instructions

### Services

| Service | Required | How to run |
|---------|----------|------------|
| Bot process | Yes (for full E2E) | `BOT_TOKEN=<token> python3 bot.py` |
| Telegram Bot API | Yes (external) | Needs valid `BOT_TOKEN` from [@BotFather](https://t.me/BotFather) |
| Java, apktool, zipalign, AndResGuard | Yes (for APK pipeline) | See `scripts/install_system_deps.sh` |

There is no web server, database, docker-compose, or test/lint framework in this repo.

### First-time system setup

On a fresh VM, install the Android toolchain once:

```bash
bash scripts/install_system_deps.sh
pip3 install --user -r requirements.txt
```

**AndResGuard note:** The `Dockerfile` downloads `AndResGuard-cli-1.2.21.jar`, but that release asset no longer exists on GitHub (404). The install script copies `AndResGuard-cli-1.2.15.jar` from the upstream repo's `tool_output/` directory instead. The config embedded in `bot.py` uses a newer `<resguard>` XML format that may not be fully compatible with 1.2.15 (whitelist paths need full package names; `use7zip` without `usesign` fails). Use `scripts/verify_pipeline.sh` to test the toolchain with a compatible config.

### Running the bot

```bash
export BOT_TOKEN="your-telegram-bot-token"
python3 bot.py
```

The bot uses Telegram long polling. Send `/start`, then upload an `.apk` document.

### Verifying the APK pipeline (no Telegram required)

```bash
# Download a sample APK if needed
wget -O /tmp/test_input.apk \
  https://github.com/appium/android-apidemos/releases/download/v6.0.15/ApiDemos-debug.apk

bash scripts/verify_pipeline.sh /tmp/test_input.apk
# Output: /tmp/randomized_output.apk
```

### Docker alternative

```bash
docker build -t apk-signer .
docker run -e BOT_TOKEN=<token> apk-signer
```

Note: the Docker build will fail at the AndResGuard download step unless the Dockerfile URL is fixed.

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from BotFather |
