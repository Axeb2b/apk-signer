import os
import random
import string
import subprocess
import shutil
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")  # Render environment variable
logging.basicConfig(level=logging.INFO)

def random_hex(length=8):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

def randomize_apk(input_path, output_path):
    work_dir = f"work_{random_hex(6)}"
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. Decompile
    subprocess.run(["apktool", "d", input_path, "-o", f"{work_dir}/dec"], check=True, capture_output=True)
    
    # 2. Random dummy file in assets
    assets_dir = f"{work_dir}/dec/assets"
    os.makedirs(assets_dir, exist_ok=True)
    dummy_name = f"r_{random_hex(8)}.bin"
    with open(f"{assets_dir}/{dummy_name}", "wb") as f:
        f.write(os.urandom(random.randint(64, 1024)))
    
    # 3. Random rename some .png in drawable (basic obfuscation, avoid XML references)
    res_dir = f"{work_dir}/dec/res"
    for root, dirs, files in os.walk(res_dir):
        if 'drawable' in root:
            pngs = [f for f in files if f.endswith('.png') and not f.startswith('abc_')]
            for old in random.sample(pngs, min(3, len(pngs))):
                ext = old.split('.')[-1]
                new = random_hex(6) + '.' + ext
                os.rename(os.path.join(root, old), os.path.join(root, new))
    
    # 4. Recompile
    subprocess.run(["apktool", "b", f"{work_dir}/dec", "-o", f"{work_dir}/unsigned.apk"], check=True, capture_output=True)
    
    # 5. Random keystore generate
    keystore = f"{work_dir}/random.keystore"
    alias = "rnd"
    storepass = random_hex(12)
    subprocess.run([
        "keytool", "-genkey", "-v", "-keystore", keystore, "-alias", alias,
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
        "-dname", "CN=Random, OU=Random, O=Random, L=Random, ST=Random, C=IN",
        "-storepass", storepass, "-keypass", storepass
    ], check=True, capture_output=True)
    
    # 6. Sign
    subprocess.run([
        "jarsigner", "-verbose", "-sigalg", "SHA1withRSA", "-digestalg", "SHA1",
        "-keystore", keystore, "-storepass", storepass, "-keypass", storepass,
        f"{work_dir}/unsigned.apk", alias
    ], check=True, capture_output=True)
    
    # 7. Align
    subprocess.run(["zipalign", "-v", "-p", "4", f"{work_dir}/unsigned.apk", output_path], check=True, capture_output=True)
    
    # Cleanup
    shutil.rmtree(work_dir)
    return output_path

async def handle_apk(update: Update, context):
    if not update.message.document:
        return
    file = await update.message.document.get_file()
    input_apk = f"in_{random_hex(6)}.apk"
    await file.download_to_drive(input_apk)
    await update.message.reply_text("🔧 Randomizing APK... (may take 20-40 sec)")
    try:
        out_apk = f"out_{random_hex(6)}.apk"
        randomize_apk(input_apk, out_apk)
        with open(out_apk, 'rb') as f:
            await update.message.reply_document(document=f, filename=out_apk)
        os.remove(out_apk)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        os.remove(input_apk)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.APK, handle_apk))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
