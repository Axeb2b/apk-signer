#!/usr/bin/env python3
"""Complete Telegram login after QR scan when 2FA password is required."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from env_loader import load_dotenv

load_dotenv()

from telethon.errors import SessionPasswordNeededError
from telegram_account import SESSION_PATH, _session


async def main() -> None:
    password = os.environ.get("TG_PASSWORD", "").strip()
    if not password:
        print("Error: TG_PASSWORD not set in .env", file=sys.stderr)
        sys.exit(1)

    async with _session() as client:
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Already logged in as {me.first_name} (@{me.username or 'no-username'}) id={me.id}")
            return

        try:
            await client.sign_in(password=password)
        except SessionPasswordNeededError:
            print("Still need QR scan. Run scripts/telegram_qr_login.py again.", file=sys.stderr)
            sys.exit(1)

        me = await client.get_me()
        print(f"Logged in as {me.first_name} (@{me.username or 'no-username'}) id={me.id}")
        print(f"Session saved to {SESSION_PATH}.session")


if __name__ == "__main__":
    asyncio.run(main())
