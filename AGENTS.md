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

### Telegram user account (full MTProto)

`telegram_account.py` manages a **user account** (not the bot) via Telethon using `TG_API_ID` / `TG_API_HASH`.

```bash
set -a && source .env && set +a
pip3 install --user -r requirements.txt

# First-time login (interactive, or set TG_PHONE / TG_CODE / TG_PASSWORD)
python3 telegram_account.py login

# Account management
python3 telegram_account.py me
python3 telegram_account.py dialogs
python3 telegram_account.py contacts
python3 telegram_account.py history @username --limit 20
python3 telegram_account.py send @username "Hello"
python3 telegram_account.py read @username
python3 telegram_account.py sessions
python3 telegram_account.py profile --about "New bio"
python3 telegram_account.py logout
```

Session files are stored in `.telegram/` (gitignored). The bot (`bot.py`) and user account manager are separate: the bot uses `BOT_TOKEN`; the account manager uses API id/hash + phone login.

### Running the bot

Credentials live in `.env` (gitignored). Copy `.env.example` if needed:

```bash
cp .env.example .env   # then edit values
set -a && source .env && set +a
python3 bot.py
```

Or export manually:

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
| `TG_API_ID` | Yes* | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `TG_API_HASH` | Yes* | Telegram API hash from [my.telegram.org](https://my.telegram.org) |
| `TG_PHONE` | Login | Phone number for `telegram_account.py login` (international format) |
| `TG_CODE` | Login | OTP code (optional; prompts if unset) |
| `TG_PASSWORD` | Login | 2FA password (optional; prompts if needed) |

\*Required for `telegram_account.py`. Not used by `bot.py` (Bot API only needs `BOT_TOKEN`).
