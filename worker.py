import time
import os
import json
import logging
from vodio_uploader import VodioUploader

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
INBOX_DIR = "inbox"
SECRETS_PATH = "/data/secrets.json"
if not os.path.exists("/data"):
    SECRETS_PATH = "secrets.json"

def get_secrets():
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def process_queue():
    logging.info("🚀 Worker started. Watching queue...")
    
    while True:
        try:
            secrets = get_secrets()
            if not secrets.get("vodio_login") or not secrets.get("vodio_password"):
                time.sleep(10)
                continue

            # Look for JSON job files
            files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".json")]
            
            for filename in files:
                file_path = os.path.join(INBOX_DIR, filename)
                
                with open(file_path, "r") as f:
                    job = json.load(f)
                
                if job.get("status") == "pending":
                    logging.info(f"🎙️ Processing job: {job['title']}")
                    
                    mp3_path = os.path.join(INBOX_DIR, job["mp3_file"])
                    
                    if os.path.exists(mp3_path):
                        uploader = VodioUploader(headless=True)
                        success = uploader.upload_episode(
                            secrets["vodio_login"],
                            secrets["vodio_password"],
                            mp3_path,
                            job["title"],
                            job["description"]
                        )
                        
                        if success:
                            job["status"] = "done"
                            logging.info(f"✅ Success: {job['title']}")
                            
                            # Cleanup (Optional: remove files after upload)
                            # os.remove(mp3_path)
                            # os.remove(file_path)
                        else:
                            job["status"] = "failed"
                            logging.error(f"❌ Failed: {job['title']}")
                            
                        # Update status
                        with open(file_path, "w") as f:
                            json.dump(job, f, indent=4)
                    else:
                        logging.error(f"⚠️ Audio file missing for {job['title']}")
                        
            time.sleep(10) # Wait before next check

        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    process_queue()
