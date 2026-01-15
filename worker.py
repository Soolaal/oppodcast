import time
import os
import json
import logging
from vodio_uploader import VodioUploader

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- GESTION DES CHEMINS (UNIFIE AVEC L'APP) ---
if os.path.exists("/share"):
    BASE_DIR = "/share/oppodcast"
else:
    BASE_DIR = os.getcwd()

INBOX_DIR = os.path.join(BASE_DIR, "inbox")
SECRETS_PATH = os.path.join(BASE_DIR, "secrets.json")

# Création du dossier inbox s'il n'existe pas (sécurité)
if not os.path.exists(INBOX_DIR):
    os.makedirs(INBOX_DIR, exist_ok=True)

def get_secrets():
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def process_queue():
    logging.info(f"Worker started. Watching directory: {INBOX_DIR}")
    
    while True:
        try:
            secrets = get_secrets()
            if not secrets.get("vodio_login") or not secrets.get("vodio_password"):
                # On attend que l'utilisateur configure ses secrets
                time.sleep(10)
                continue

            # Look for JSON job files
            if os.path.exists(INBOX_DIR):
                files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".json")]
                
                for filename in files:
                    file_path = os.path.join(INBOX_DIR, filename)
                    
                    with open(file_path, "r") as f:
                        job = json.load(f)
                    
                    if job.get("status") == "pending":
                        logging.info(f"Processing job: {job['title']}")
                        
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
                                logging.info(f"Success: {job['title']}")
                            else:
                                job["status"] = "failed"
                                logging.error(f"Failed: {job['title']}")
                                
                            # Update status
                            with open(file_path, "w") as f:
                                json.dump(job, f, indent=4)
                        else:
                            logging.error(f"Audio file missing for {job['title']}")
                            
            time.sleep(10) # Wait before next check

        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    process_queue()
