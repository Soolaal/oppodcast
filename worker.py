import time
import glob
import json
import os
import shutil
import sys
from datetime import datetime

# --- CONFIGURATION & SECRETS ---
SECRETS_PATH = "/data/secrets.json"
# Fallback for local testing
if not os.path.exists("/data"):
    SECRETS_PATH = "secrets.json"

def get_secrets():
    """Retrieve credentials from persistent JSON."""
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r") as f:
                data = json.load(f)
                login = data.get("vodio_login")
                password = data.get("vodio_password")
                if login and password:
                    return login, password
        except:
            pass
    return None, None

try:
    from vodio_uploader import VodioUploader
except ImportError:
    print("Error: vodio_uploader.py missing!")
    sys.exit(1)

# --- DIRECTORIES ---
INBOX_DIR = "inbox"
PROCESSED_DIR = "processed"
FAILED_DIR = "failed"

for d in [INBOX_DIR, PROCESSED_DIR, FAILED_DIR]:
    os.makedirs(d, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def process_job(json_path):
    # 1. Read JSON job file
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            job_data = json.load(f)
    except Exception as e:
        log(f"Invalid JSON: {e}")
        shutil.move(json_path, os.path.join(FAILED_DIR, os.path.basename(json_path)))
        return

    # 2. Get Credentials
    login_vodio, password_vodio = get_secrets()

    if not login_vodio:
        log("CRITICAL ERROR: Missing Vodio credentials! Please configure the app.")
        time.sleep(10) 
        return

    # 3. Extract Info
    title = job_data.get('title', 'Untitled')
    audio_filename = job_data.get('mp3_file')
    description = job_data.get('description', '')
    
    audio_path = os.path.join(INBOX_DIR, audio_filename)
    
    # 4. Check Audio File
    if not os.path.exists(audio_path):
        log(f"Audio file not found: {audio_filename}")
        shutil.move(json_path, os.path.join(FAILED_DIR, os.path.basename(json_path)))
        return

    log(f"Starting job: '{title}'")

    try:
        log(f"Connecting to Vodio as: {login_vodio}...")
        
        # Instantiate uploader (Headless = True for production/Docker)
        uploader = VodioUploader(login_vodio, password_vodio, headless=True)
        
        success = uploader.upload(audio_path, title, description)
        
        if success:
            log(f"Success! Episode '{title}' processed.")
            
            # --- ARCHIVE (Success) ---
            target_json = os.path.join(PROCESSED_DIR, os.path.basename(json_path))
            target_audio = os.path.join(PROCESSED_DIR, os.path.basename(audio_path))
            
            if os.path.exists(target_json): os.remove(target_json)
            if os.path.exists(target_audio): os.remove(target_audio)
            
            shutil.move(json_path, target_json)
            shutil.move(audio_path, target_audio)
        else:
            raise Exception("Upload returned False (unknown error)")

    except Exception as e:
        log(f"ERROR during processing: {e}")
        
        # --- ERROR HANDLING (Failed) ---
        target_json = os.path.join(FAILED_DIR, os.path.basename(json_path))
        target_audio = os.path.join(FAILED_DIR, os.path.basename(audio_path))

        if os.path.exists(target_json): os.remove(target_json)
        shutil.move(json_path, target_json)
        
        if os.path.exists(audio_path):
            if os.path.exists(target_audio): os.remove(target_audio)
            shutil.move(audio_path, target_audio)

# --- MAIN LOOP ---
if __name__ == "__main__":
    log("Worker STARTED - Waiting for jobs...")
    
    login_check, _ = get_secrets()
    if login_check:
        log(f"Configuration detected for user: {login_check}")
    else:
        log("No configuration found. Waiting for user input via interface...")

    try:
        while True:
            job_files = glob.glob(os.path.join(INBOX_DIR, "*.json"))
            
            if job_files:
                for job in job_files:
                    process_job(job)
            else:
                time.sleep(5)
                
    except KeyboardInterrupt:
        log("Worker stopped.")
