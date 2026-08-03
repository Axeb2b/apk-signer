# AGENTS.md

## Cursor Cloud specific instructions

### Unblock checklist

1. **System deps** (once per VM): `bash scripts/install_system_deps.sh`
2. **Python deps**: `pip3 install --user -r requirements.txt`
3. **Secrets in `.env`**: `BOT_TOKEN` required for `bot.py`; `TG_API_ID` / `TG_API_HASH` for `telegram_account.py`
4. **Verify toolchain**: `bash scripts/verify_pipeline.sh /tmp/test_input.apk`

`bot.py` and `env_loader.py` auto-load `.env` on startup.

### Known fixes (PR #4)

- **Dockerfile**: AndResGuard 1.2.21 URL was 404 — now clones upstream and uses `AndResGuard-cli-1.2.15.jar`
- **bot.py**: AndResGuard config updated to `<resproguard>` format compatible with 1.2.15
- **bot.py**: `zipalign` now runs on `recompiled.apk` (jarsigner signs in place; `signed.apk` never existed)

### Running the bot

```bash
set -a && source .env && set +a
python3 bot.py
```
