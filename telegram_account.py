#!/usr/bin/env python3
"""Telegram user-account manager (MTProto via Telethon).

Uses TG_API_ID and TG_API_HASH from the environment. Session is stored under
.telegram/session (gitignored).

Examples:
  python3 telegram_account.py login
  python3 telegram_account.py me
  python3 telegram_account.py dialogs
  python3 telegram_account.py send @username "Hello"
  python3 telegram_account.py history @username --limit 20
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from datetime import timezone
from pathlib import Path

from env_loader import load_dotenv

load_dotenv()

from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import SQLiteSession

SESSION_DIR = Path(__file__).resolve().parent / ".telegram"
SESSION_PATH = str(SESSION_DIR / "session")


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"Error: {name} is not set. Add it to .env or export it.", file=sys.stderr)
        sys.exit(1)
    return value


def _api_id() -> int:
    return int(_require_env("TG_API_ID"))


def _api_hash() -> str:
    return _require_env("TG_API_HASH")


def _client() -> TelegramClient:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return TelegramClient(SQLiteSession(SESSION_PATH), _api_id(), _api_hash())


def _prompt(label: str, secret: bool = False) -> str:
    if secret:
        import getpass

        return getpass.getpass(f"{label}: ").strip()
    return input(f"{label}: ").strip()


async def _ensure_authorized(client: TelegramClient) -> None:
    if await client.is_user_authorized():
        return
    print("Not logged in. Run: python3 telegram_account.py login", file=sys.stderr)
    sys.exit(1)


@asynccontextmanager
async def _session():
    client = _client()
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()


async def cmd_send_code(_: argparse.Namespace) -> None:
    phone = os.environ.get("TG_PHONE", "").strip() or _prompt("Phone number (international, e.g. +15551234567)")

    async with _session() as client:
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Already logged in as {me.first_name} (@{me.username or 'no-username'}) id={me.id}")
            return

        sent = await client.send_code_request(phone)
        delivery = type(sent.type).__name__
        print(f"OTP sent to {phone}")
        print(f"Delivery: {delivery}")
        if "App" in delivery:
            print("Check the Telegram app on your phone for a message from 'Telegram' (not SMS).")
        else:
            print("Check SMS or Telegram for your login code.")
        print("Then run: TG_CODE=<code> python3 telegram_account.py verify-code")


async def cmd_verify_code(_: argparse.Namespace) -> None:
    phone = os.environ.get("TG_PHONE", "").strip() or _prompt("Phone number (international, e.g. +15551234567)")
    code = os.environ.get("TG_CODE", "").strip() or _prompt("Login code from Telegram")

    async with _session() as client:
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Already logged in as {me.first_name} (@{me.username or 'no-username'}) id={me.id}")
            return

        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = os.environ.get("TG_PASSWORD", "").strip() or _prompt(
                "Two-step verification password", secret=True
            )
            await client.sign_in(password=password)

        me = await client.get_me()
        print(f"Logged in as {me.first_name} (@{me.username or 'no-username'}) id={me.id}")
        print(f"Session saved to {SESSION_PATH}.session")


async def cmd_login(_: argparse.Namespace) -> None:
    if os.environ.get("TG_CODE", "").strip():
        await cmd_verify_code(_)
        return
    await cmd_send_code(_)


async def cmd_logout(_: argparse.Namespace) -> None:
    async with _session() as client:
        if await client.is_user_authorized():
            await client.log_out()
            print("Logged out from Telegram.")
    for path in SESSION_DIR.glob("session*"):
        path.unlink(missing_ok=True)
    print("Local session files removed.")


async def cmd_me(_: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        me = await client.get_me()
        full = await client(functions.users.GetFullUserRequest(me))
        print(f"ID:       {me.id}")
        print(f"Name:     {me.first_name or ''} {me.last_name or ''}".strip())
        print(f"Username: @{me.username}" if me.username else "Username: (none)")
        print(f"Phone:    {me.phone or '(hidden)'}")
        print(f"Premium:  {me.premium}")
        print(f"Bot:      {me.bot}")
        bio = full.full_user.about or ""
        print(f"Bio:      {bio or '(empty)'}")


async def cmd_dialogs(args: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        count = 0
        async for dialog in client.iter_dialogs(limit=args.limit):
            entity = dialog.entity
            kind = type(entity).__name__.replace("Channel", "channel").replace("Chat", "group").replace("User", "user")
            username = getattr(entity, "username", None)
            label = f"@{username}" if username else str(dialog.id)
            unread = f" [{dialog.unread_count} unread]" if dialog.unread_count else ""
            print(f"{dialog.id:>14}  {kind:8}  {label:24}  {dialog.title or ''}{unread}")
            count += 1
        print(f"\n{count} dialog(s)")


async def cmd_contacts(args: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        result = await client(functions.contacts.GetContactsRequest(hash=0))
        users = result.users[: args.limit]
        for user in users:
            username = f"@{user.username}" if user.username else ""
            phone = user.phone or ""
            print(f"{user.id:>14}  {user.first_name or ''} {user.last_name or ''}  {username}  {phone}")
        print(f"\n{len(users)} contact(s) shown")


async def cmd_history(args: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        entity = await client.get_entity(args.chat)
        async for message in client.iter_messages(entity, limit=args.limit):
            when = message.date.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            sender = "me" if message.out else getattr(message.sender, "username", None) or message.sender_id
            text = (message.text or message.message or "").replace("\n", " ")
            if len(text) > 120:
                text = text[:117] + "..."
            media = f" [{type(message.media).__name__}]" if message.media else ""
            print(f"{when}  {sender}: {text}{media}")


async def cmd_send(args: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        entity = await client.get_entity(args.chat)
        msg = await client.send_message(entity, args.text)
        print(f"Sent message id={msg.id} to {args.chat}")


async def cmd_read(args: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        entity = await client.get_entity(args.chat)
        await client.send_read_acknowledge(entity, max_id=args.max_id)
        print(f"Marked messages as read in {args.chat}")


async def cmd_profile(args: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        me = await client.get_me()
        updates = []

        if args.first_name is not None:
            me.first_name = args.first_name
            updates.append("first_name")
        if args.last_name is not None:
            me.last_name = args.last_name
            updates.append("last_name")
        if args.about is not None:
            await client(functions.account.UpdateProfileRequest(about=args.about))
            updates.append("about")

        if updates:
            if args.first_name is not None or args.last_name is not None:
                await client(functions.account.UpdateProfileRequest(
                    first_name=me.first_name,
                    last_name=me.last_name,
                ))
            print(f"Updated: {', '.join(updates)}")
        else:
            await cmd_me(args)


async def cmd_delete_messages(args: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        entity = await client.get_entity(args.chat)
        ids = [int(x) for x in args.ids]
        await client.delete_messages(entity, ids)
        print(f"Deleted {len(ids)} message(s) in {args.chat}")


async def cmd_sessions(_: argparse.Namespace) -> None:
    async with _session() as client:
        await _ensure_authorized(client)
        result = await client(functions.account.GetAuthorizationsRequest())
        for auth in result.authorizations:
            current = " (this device)" if auth.current else ""
            print(
                f"{auth.hash}  {auth.device_model} / {auth.platform} / {auth.app_name}"
                f"  {auth.country}  {auth.date_active}{current}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a Telegram user account via MTProto")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("login", help="Authenticate with phone + OTP and save session")
    sub.add_parser("send-code", help="Send OTP to phone (step 1)")
    sub.add_parser("verify-code", help="Complete login with TG_CODE (step 2)")
    sub.add_parser("logout", help="Log out and remove local session")
    sub.add_parser("me", help="Show account profile")
    sub.add_parser("sessions", help="List active account sessions")

    p = sub.add_parser("dialogs", help="List recent chats")
    p.add_argument("--limit", type=int, default=50)

    p = sub.add_parser("contacts", help="List contacts")
    p.add_argument("--limit", type=int, default=100)

    p = sub.add_parser("history", help="Show recent messages in a chat")
    p.add_argument("chat", help="Username (@name), phone, or numeric chat id")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("send", help="Send a text message")
    p.add_argument("chat", help="Username (@name), phone, or numeric chat id")
    p.add_argument("text", help="Message text")

    p = sub.add_parser("read", help="Mark chat messages as read")
    p.add_argument("chat", help="Username (@name), phone, or numeric chat id")
    p.add_argument("--max-id", type=int, default=0, dest="max_id")

    p = sub.add_parser("delete", help="Delete messages by id")
    p.add_argument("chat")
    p.add_argument("ids", nargs="+", help="Message id(s)")

    p = sub.add_parser("profile", help="Show or update profile fields")
    p.add_argument("--first-name", dest="first_name")
    p.add_argument("--last-name", dest="last_name")
    p.add_argument("--about", help="Bio / about text")

    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handlers = {
        "login": cmd_login,
        "send-code": cmd_send_code,
        "verify-code": cmd_verify_code,
        "logout": cmd_logout,
        "me": cmd_me,
        "sessions": cmd_sessions,
        "dialogs": cmd_dialogs,
        "contacts": cmd_contacts,
        "history": cmd_history,
        "send": cmd_send,
        "read": cmd_read,
        "delete": cmd_delete_messages,
        "profile": cmd_profile,
    }
    await handlers[args.command](args)


if __name__ == "__main__":
    asyncio.run(main())
