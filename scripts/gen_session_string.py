#!/usr/bin/env python3
"""Run this ON YOUR PHONE OR PC (not the cloud VM) to create a session string.

Install: pip install telethon

Usage:
  export TG_API_ID=33100108
  export TG_API_HASH=9a5e62c7dc7123ea1746df18050d9fc5
  python3 gen_session_string.py

Telegram will send an OTP to your phone (official app flow — usually SMS works there).
Copy the printed session string and send it to the agent, or add to .env:

  TG_SESSION_STRING=1BVtsOHwBu5X...

Then on the VM:
  python3 telegram_account.py import-session
"""

from __future__ import annotations

import asyncio
import os

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    phone = os.environ.get("TG_PHONE", "").strip() or input("Phone (+919...): ").strip()

    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        await client.start(phone=phone)
        me = await client.get_me()
        print(f"\nLogged in as {me.first_name} (@{me.username or 'no-username'})")
        print("\nCopy this session string (keep it secret):\n")
        print(client.session.save())


if __name__ == "__main__":
    asyncio.run(main())
