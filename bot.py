import os
import random
import string
import subprocess
import shutil
import tempfile
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise Exception("BOT_TOKEN not set")

logging.basicConfig(level=logging.INFO)

def random_hex(n=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

AND_RES_GUARD_JAR = "/opt/AndResGuard.jar"

async def start(update: Update, context):
    await update.message.reply_text("Send me an APK. I will obfuscate resources (AndResGuard), add random dummy, and random sign.")

async def handle_apk(update: Update, context):
    if not update.message.document:
        return
    msg = await update.message.reply_text("Downloading APK...")
    file = await update.message.document.get_file()
    input_apk = f"in_{random_hex()}.apk"
    await file.download_to_drive(input_apk)

    try:
        # 1. AndResGuard
        await msg.edit_text("Obfuscating resources with AndResGuard...")
        work_dir = tempfile.mkdtemp()
        out_dir = os.path.join(work_dir, "andres_out")
        os.makedirs(out_dir, exist_ok=True)

        config = """<?xml version="1.0" encoding="UTF-8"?>
<resguard>
    <issue id="whitelist" isactive="true">
        <path value="R.drawable.ic_launcher" />
        <path value="R.mipmap.ic_launcher" />
        <path value="R.string.app_name" />
    </issue>
    <issue id="compress" isactive="true">
        <path value="*.png" />
        <path value="*.jpg" />
        <path value="*.jpeg" />
        <path value="*.gif" />
    </issue>
    <issue id="use7zip" isactive="true" />
    <issue id="usesign" isactive="false" />
    <issue id="keeproot" isactive="false" />
    <issue id="mergeres" isactive="true" />
</resguard>"""
        config_path = os.path.join(work_dir, "config.xml")
        with open(config_path, "w") as f:
            f.write(config)

        subprocess.run([
            "java", "-jar", AND_RES_GUARD_JAR,
            input_apk,
            "-config", config_path,
            "-out", out_dir
        ], check=True, capture_output=True)

        # Find unsigned obfuscated APK
        obf_apk = None
        for f in os.listdir(out_dir):
            if f.endswith(".apk") and "unsigned" in f:
                obf_apk = os.path.join(out_dir, f)
                break
        if not obf_apk:
            raise Exception("AndResGuard output not found")

        # 2. Decompile and add random dummy asset
        await msg.edit_text("Adding random dummy asset...")
        dec_dir = os.path.join(work_dir, "dec")
        subprocess.run(["apktool", "d", obf_apk, "-o", dec_dir], check=True, capture_output=True)
        assets_dir = os.path.join(dec_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        dummy = f"r_{random_hex(8)}.bin"
        with open(os.path.join(assets_dir, dummy), "wb") as f:
            f.write(os.urandom(256))

        recompiled = os.path.join(work_dir, "recompiled.apk")
        subprocess.run(["apktool", "b", dec_dir, "-o", recompiled], check=True, capture_output=True)

        # 3. Random sign + zipalign
        await msg.edit_text("Random signing...")
        keystore = os.path.join(work_dir, "random.keystore")
        alias = "rnd"
        storepass = random_hex(12)
        subprocess.run([
            "keytool", "-genkey", "-v", "-keystore", keystore, "-alias", alias,
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-dname", "CN=Random, OU=Random, O=Random, L=Random, ST=Random, C=IN",
            "-storepass", storepass, "-keypass", storepass
        ], check=True, capture_output=True)

        signed = os.path.join(work_dir, "signed.apk")
        subprocess.run([
            "jarsigner", "-verbose", "-sigalg", "SHA1withRSA", "-digestalg", "SHA1",
            "-keystore", keystore, "-storepass", storepass, "-keypass", storepass,
            recompiled, alias
        ], check=True, capture_output=True)

        final_apk = os.path.join(work_dir, "final.apk")
        try:
            subprocess.run(["zipalign", "-v", "-p", "4", signed, final_apk], check=True, capture_output=True)
        except FileNotFoundError:
            final_apk = signed

        await msg.edit_text("Sending back...")
        with open(final_apk, "rb") as f:
            await update.message.reply_document(document=f, filename=f"randomized_{random_hex()}.apk")

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")
        logging.exception("APK processing failed")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        os.remove(input_apk)
        await msg.delete()

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.APK, handle_apk))
    print("Bot started (no Flask, pure polling). Send APK via Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()
