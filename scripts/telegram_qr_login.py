#!/usr/bin/env python3
"""QR login for Telegram — scan from Telegram app: Settings → Devices → Link Desktop Device."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import qrcode
from telethon.errors import SessionPasswordNeededError

from env_loader import load_dotenv

load_dotenv()

from telegram_account import SESSION_PATH, _session  # noqa: E402

QR_PATH = Path("/opt/cursor/artifacts/telegram_login_qr.png")
REFRESH_BUFFER_SEC = 3


def save_qr(url: str) -> Path:
    QR_PATH.parent.mkdir(parents=True, exist_ok=True)
    img = qrcode.make(url)
    img.save(QR_PATH)
    return QR_PATH


def _print_qr_instructions(path: Path, url: str, *, refreshed: bool = False) -> None:
    prefix = "QR refreshed" if refreshed else "QR saved"
    print(f"{prefix}: {path}", flush=True)
    print("On your phone: Telegram → Settings → Devices → Link Desktop Device → scan QR", flush=True)
    print(f"Or open this link on the phone: {url}", flush=True)


async def _wait_for_qr_scan(qr_login, timeout: int) -> None:
    """Wait for scan, refreshing the QR before each ~30s token expiry."""
    deadline = time.monotonic() + timeout
    first = True

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise asyncio.TimeoutError()

        until_expiry = (qr_login.expires - datetime.now(timezone.utc)).total_seconds()
        if until_expiry <= REFRESH_BUFFER_SEC:
            await qr_login.recreate()
            _print_qr_instructions(save_qr(qr_login.url), qr_login.url, refreshed=not first)
            first = False
            continue

        wait_for = min(remaining, until_expiry - REFRESH_BUFFER_SEC)
        try:
            await qr_login.wait(timeout=wait_for)
            return
        except asyncio.TimeoutError:
            continue


async def main() -> None:
    timeout = int(os.environ.get("TG_QR_TIMEOUT", "180"))

    async with _session() as client:
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Already logged in as {me.first_name} (@{me.username or 'no-username'}) id={me.id}")
            return

        qr_login = await client.qr_login()
        _print_qr_instructions(save_qr(qr_login.url), qr_login.url)
        print(f"Waiting up to {timeout}s for scan (QR auto-refreshes every ~30s)...", flush=True)

        try:
            await _wait_for_qr_scan(qr_login, timeout)
        except SessionPasswordNeededError:
            password = os.environ.get("TG_PASSWORD", "").strip()
            if not password:
                print("2FA required. Set TG_PASSWORD in .env and run again.", file=sys.stderr)
                sys.exit(1)
            await client.sign_in(password=password)
        except asyncio.TimeoutError:
            print("QR not scanned in time. Run this script again.", file=sys.stderr)
            sys.exit(1)

        me = await client.get_me()
        print(f"Logged in as {me.first_name} (@{me.username or 'no-username'}) id={me.id}")
        print(f"Session saved to {SESSION_PATH}.session")


if __name__ == "__main__":
    asyncio.run(main())
