import os
import random
import string
import subprocess
import shutil
import tempfile
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

def random_hex(length=8):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

def run_andresguard(input_apk, output_apk):
    """Run AndResGuard to obfuscate resources, output unsigned APK"""
    # Create temporary config file for AndResGuard
    config_content = """<?xml version="1.0" encoding="UTF-8"?>
<resguard>
    <issue id="whitelist" isactive="true">
        <path value="R.drawable.icon" />  <!-- keep your launcher icon -->
        <path value="R.string.app_name" />
        <!-- Add any other kept resources if needed -->
    </issue>
    <issue id="compress" isactive="true">
        <path value="*.png" />
        <path value="*.jpg" />
        <path value="*.jpeg" />
        <path value="*.gif" />
    </issue>
    <issue id="use7zip" isactive="true" />
    <issue id="usesign" isactive="false" />   <!-- we'll sign later -->
    <issue id="keeproot" isactive="false" />
    <issue id="mergeres" isactive="true" />
</resguard>"""
    config_path = "/app/andresguard-config/config.xml"
    with open(config_path, "w") as f:
        f.write(config_content)
    
    # Run AndResGuard
    out_dir = tempfile.mkdtemp()
    cmd = [
        "java", "-jar", "/opt/AndResGuard.jar",
        input_apk,
        "-config", config_path,
        "-out", out_dir,
        "-signature", "false"   # ensure no signing
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Find the generated APK (AndResGuard names it like input_unsigned.apk or something)
    for f in os.listdir(out_dir):
        if f.endswith(".apk") and "unsigned" in f:
            shutil.move(os.path.join(out_dir, f), output_apk)
            break
    shutil.rmtree(out_dir)
    return output_apk

def add_dummy_asset_and_recompile(input_apk, output_apk):
    """Decompile APK, add random dummy file to assets, recompile (unsigned)"""
    work_dir = tempfile.mkdtemp()
    dec_dir = os.path.join(work_dir, "dec")
    subprocess.run(["apktool", "d", input_apk, "-o", dec_dir], check=True, capture_output=True)
    
    # Add random dummy file
    assets_dir = os.path.join(dec_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    dummy_name = f"r_{random_hex(8)}.bin"
    with open(os.path.join(assets_dir, dummy_name), "wb") as f:
        f.write(os.urandom(random.randint(64, 1024)))
    
    # Recompile
    unsigned_apk = os.path.join(work_dir, "unsigned.apk")
    subprocess.run(["apktool", "b", dec_dir, "-o", unsigned_apk], check=True, capture_output=True)
    
    shutil.move(unsigned_apk, output_apk)
    shutil.rmtree(work_dir)
    return output_apk

def random_sign_and_align(input_apk, output_apk):
    """Generate random keystore, sign APK, and zipalign"""
    work_dir = tempfile.mkdtemp()
    keystore = os.path.join(work_dir, "random.keystore")
    alias = "rnd"
    storepass = random_hex(12)
    keypass = storepass
    
    # Generate keystore
    subprocess.run([
        "keytool", "-genkey", "-v", "-keystore", keystore, "-alias", alias,
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
        "-dname", "CN=Random, OU=Random, O=Random, L=Random, ST=Random, C=IN",
        "-storepass", storepass, "-keypass", keypass
    ], check=True, capture_output=True)
    
    # Sign
    signed_apk = os.path.join(work_dir, "signed.apk")
    subprocess.run([
        "jarsigner", "-verbose", "-sigalg", "SHA1withRSA", "-digestalg", "SHA1",
        "-keystore", keystore, "-storepass", storepass, "-keypass", keypass,
        input_apk, alias
    ], check=True, capture_output=True)
    
    # Zipalign
    subprocess.run(["zipalign", "-v", "-p", "4", input_apk, output_apk], check=True, capture_output=True)
    
    shutil.rmtree(work_dir)
    return output_apk

async def handle_apk(update: Update, context):
    if not update.message.document:
        return
    file = await update.message.document.get_file()
    input_apk = f"in_{random_hex(6)}.apk"
    await file.download_to_drive(input_apk)
    await update.message.reply_text("🔄 Step 1/3: Resource obfuscation with AndResGuard...")
    try:
        # Step 1: AndResGuard
        obf_apk = f"obf_{random_hex(6)}.apk"
        run_andresguard(input_apk, obf_apk)
        
        # Step 2: Add dummy asset
        await update.message.reply_text("📦 Step 2/3: Adding random dummy asset...")
        asset_apk = f"asset_{random_hex(6)}.apk"
        add_dummy_asset_and_recompile(obf_apk, asset_apk)
        
        # Step 3: Random sign + align
        await update.message.reply_text("🔑 Step 3/3: Random signing...")
        final_apk = f"final_{random_hex(6)}.apk"
        random_sign_and_align(asset_apk, final_apk)
        
        # Send back
        with open(final_apk, 'rb') as f:
            await update.message.reply_document(document=f, filename=final_apk)
        # Cleanup
        os.remove(input_apk)
        os.remove(obf_apk)
        os.remove(asset_apk)
        os.remove(final_apk)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        if os.path.exists(input_apk):
            os.remove(input_apk)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.APK, handle_apk))
    print("Bot started with AndResGuard integration...")
    app.run_polling()

if __name__ == "__main__":
    main()
