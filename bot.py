import os
import random
import string
import subprocess
import shutil
import tempfile
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

def random_hex(length=8):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive! Send me an APK file to randomize.")

async def handle_apk(update: Update, context):
    if not update.message.document:
        return
    file = await update.message.document.get_file()
    input_apk = f"in_{random_hex(6)}.apk"
    await file.download_to_drive(input_apk)
    await update.message.reply_text("⏳ Processing APK... (may take 20-40 sec)")

    try:
        # Decompile
        work_dir = tempfile.mkdtemp()
        dec_dir = os.path.join(work_dir, "dec")
        subprocess.run(["apktool", "d", input_apk, "-o", dec_dir], check=True, capture_output=True)

        # Add dummy asset
        assets_dir = os.path.join(dec_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        dummy_name = f"r_{random_hex(8)}.bin"
        with open(os.path.join(assets_dir, dummy_name), "wb") as f:
            f.write(os.urandom(random.randint(64, 1024)))

        # Recompile (unsigned)
        unsigned_apk = os.path.join(work_dir, "unsigned.apk")
        subprocess.run(["apktool", "b", dec_dir, "-o", unsigned_apk], check=True, capture_output=True)

        # Random sign
        keystore = os.path.join(work_dir, "random.keystore")
        alias = "rnd"
        storepass = random_hex(12)
        subprocess.run([
            "keytool", "-genkey", "-v", "-keystore", keystore, "-alias", alias,
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-dname", "CN=Random, OU=Random, O=Random, L=Random, ST=Random, C=IN",
            "-storepass", storepass, "-keypass", storepass
        ], check=True, capture_output=True)

        signed_apk = os.path.join(work_dir, "signed.apk")
        subprocess.run([
            "jarsigner", "-verbose", "-sigalg", "SHA1withRSA", "-digestalg", "SHA1",
            "-keystore", keystore, "-storepass", storepass, "-keypass", storepass,
            unsigned_apk, alias
        ], check=True, capture_output=True)

        # Align
        final_apk = os.path.join(work_dir, "final.apk")
        subprocess.run(["zipalign", "-v", "-p", "4", signed_apk, final_apk], check=True, capture_output=True)

        # Send back
        with open(final_apk, 'rb') as f:
            await update.message.reply_document(document=f, filename=f"randomized_{random_hex(6)}.apk")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logging.exception("APK processing failed")
    finally:
        # Cleanup
        if os.path.exists(input_apk):
            os.remove(input_apk)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.APK, handle_apk))
    print("Bot started (lightweight version)...")
    app.run_polling()

if __name__ == "__main__":
    main()
