# AGENTS.md

## Project overview

Telegram APK signer bot plus user-account manager and RAG pipeline over project docs.

## Cursor Cloud specific instructions

### Unblock checklist

1. **System deps** (once per VM): `bash scripts/install_system_deps.sh`
2. **Python deps**: `pip3 install --user -r requirements.txt`
3. **Optional RAG deps**: `pip3 install --user -r requirements-rag.txt`
4. **Secrets in `.env`**: `BOT_TOKEN` for bot; `TG_API_ID`/`TG_API_HASH` for account manager
5. **Verify toolchain**: `bash scripts/verify_pipeline.sh /tmp/test_input.apk`

`bot.py`, `telegram_account.py`, and `rag_cli.py` auto-load `.env` via `env_loader.py`.

### Running the bot

```bash
python3 bot.py
```

Send `/start`, then upload an `.apk` document.

### Telegram user account

```bash
python3 telegram_account.py login
python3 telegram_account.py me
python3 telegram_account.py dialogs
python3 telegram_account.py send @username "Hello"
```

### RAG pipeline

```bash
pip3 install --user -r requirements-rag.txt
python rag_cli.py ingest --reset
python rag_cli.py query "How does APK signing work?" --show-sources
```

Set `OPENAI_API_KEY` for LLM answers; without it, query returns top retrieved chunks.

### Verifying APK pipeline (no Telegram)

```bash
wget -O /tmp/test_input.apk \
  https://github.com/appium/android-apidemos/releases/download/v6.0.15/ApiDemos-debug.apk
bash scripts/verify_pipeline.sh /tmp/test_input.apk
```

### Docker

```bash
docker build -t apk-signer .
docker run --env-file .env apk-signer
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Bot | Telegram bot token from BotFather |
| `TG_API_ID` | Account | API ID from my.telegram.org |
| `TG_API_HASH` | Account | API hash from my.telegram.org |
| `TG_PHONE` | Login | Phone for account login |
| `TG_CODE` | Login | OTP code (optional) |
| `TG_PASSWORD` | Login | 2FA password (optional) |
| `OPENAI_API_KEY` | RAG | LLM answer generation |
| `RAG_LLM_MODEL` | RAG | Default `gpt-4o-mini` |
