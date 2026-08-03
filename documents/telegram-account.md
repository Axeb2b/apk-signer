# Telegram Account Manager

`telegram_account.py` manages a full Telegram **user account** via MTProto (Telethon).

## Authentication

Requires `TG_API_ID` and `TG_API_HASH` from https://my.telegram.org

Login flow:
1. Run `python3 telegram_account.py login`
2. Enter phone number (international format, e.g. +15551234567)
3. Enter OTP code sent by Telegram
4. Enter 2FA password if enabled

Session is saved in `.telegram/session` (gitignored).

## Commands

| Command | Description |
|---------|-------------|
| `login` | Authenticate and save session |
| `logout` | Log out and remove session |
| `me` | Show profile info |
| `dialogs` | List recent chats |
| `contacts` | List contacts |
| `history <chat>` | Show recent messages |
| `send <chat> <text>` | Send a message |
| `read <chat>` | Mark messages as read |
| `delete <chat> <ids>` | Delete messages by ID |
| `profile` | View or update name/bio |
| `sessions` | List active device sessions |

## Difference from the bot

- `bot.py` uses **Bot API** with `BOT_TOKEN` — for automated APK processing
- `telegram_account.py` uses **User API** with API id/hash — for managing a real account
