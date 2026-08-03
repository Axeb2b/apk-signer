# apk-signer

Telegram bot that processes APK files: AndResGuard obfuscation → apktool decompile/recompile with a dummy asset → random signing → zipalign.

Also includes a Telegram user-account CLI (Telethon) and a local RAG pipeline over project docs.

## Quick start

```bash
# 1. System toolchain (Java, apktool, zipalign, AndResGuard)
bash scripts/install_system_deps.sh

# 2. Python deps
pip3 install --user -r requirements.txt

# 3. Configure secrets
cp .env.example .env   # add BOT_TOKEN, TG_API_ID, TG_API_HASH, etc.

# 4. Run the APK bot
python3 bot.py

# 5. Verify toolchain (no Telegram needed)
bash scripts/verify_pipeline.sh /tmp/test_input.apk
```

## Components

| Component | Entry point | Purpose |
|-----------|-------------|---------|
| APK bot | `bot.py` | Telegram bot — send `.apk`, get processed APK back |
| Account CLI | `telegram_account.py` | Manage Telegram user account (MTProto) |
| RAG | `rag_cli.py` | Q&A over `documents/` (optional: `requirements-rag.txt`) |

## Telegram account login

For **+91 numbers**, Telegram API often delivers OTP only inside the app (not SMS). If OTP never arrives:

1. **QR login:** `pip install qrcode[pil]` then `python3 scripts/telegram_qr_login.py`
2. **Session string:** run `scripts/gen_session_string.py` on your phone/PC, set `TG_SESSION_STRING` in `.env`, then `python3 telegram_account.py import-session`
3. **2FA after QR:** set `TG_PASSWORD` and run `python3 scripts/telegram_complete_2fa.py`

## Docker

```bash
docker build -t apk-signer .
docker run --env-file .env apk-signer
```

## Docs

See [AGENTS.md](AGENTS.md) for Cursor Cloud agent instructions.
