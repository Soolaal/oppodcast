import time
import json
import os
import traceback
import sys

# --- CONFIGURATION ---
JOBS_FILE = "jobs.json"
try:
    from youtube_generator import YouTubeGenerator
    from vodio_uploader import VodioUploader
    from shorts_generator import ShortsGenerator 
except ImportError as e:
    print(f"⚠️ Erreur d'import dans le Worker : {e}")

def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_jobs(jobs):
    """Sauvegarde atomique pour éviter la corruption de fichier"""
    temp_file = f"{JOBS_FILE}.tmp"
    with open(temp_file, "w") as f:
        json.dump(jobs, f, indent=4)
    os.replace(temp_file, JOBS_FILE)

def update_job_status(job_id, status, error_msg=None, progress=0):
    """Met à jour le statut d'un job pour l'UI"""
    jobs = load_jobs()
    if job_id in jobs:
        jobs[job_id]["status"] = status
        jobs[job_id]["progress"] = progress
        if error_msg:
            jobs[job_id]["error"] = error_msg
        
        if status in ["completed", "failed"]:
            jobs[job_id]["finished_at"] = time.time()
            
        save_jobs(jobs)

def process_video_generation(job, job_id):
    """Logique dédiée à la génération vidéo"""
    gen = YouTubeGenerator()
    
    # Callback pour mettre à jour la progress bar dans l'UI via le JSON
    def progress_callback(p):
        if p % 10 == 0:
            update_job_status(job_id, "processing", progress=p)

    output_path = gen.generate_video(
        audio_path=job["audio_path"],
        image_path=job["image_path"],
        output_filename=f"video_{job_id}.mp4",
        render_mode=job.get("render_mode", "balanced"), # Important : paramètre par défaut
        progress_callback=progress_callback
    )
    return output_path

def process_upload(job, job_id):
    """Logique d'upload"""

    secrets = load_jobs().get("secrets", {})
    
    if os.path.exists("secrets.json"):
        with open("secrets.json", "r") as f:
            secrets = json.load(f)
    else:
        raise ValueError("secrets.json introuvable pour l'upload Vodio")
        
    uploader = VodioUploader(headless=True)
    

    result = uploader.upload_episode(
        login=secrets["vodio_login"],
        password=secrets["vodio_password"],
        file_path=job["audio_path"],
        title=job["title"],
        description=job["description"]
    )
    
    if not result:
        raise Exception("Échec de l'upload Vodio (voir logs console)")
    
    return True


def main():
    print("🚀 Oppodcast Worker Démarré (Mode Local)...")
    
    while True:
        jobs = load_jobs()

        pending_job_id = None
        for jid, data in jobs.items():
            if data["status"] == "pending":
                pending_job_id = jid
                break
        
        if pending_job_id:
            job = jobs[pending_job_id]
            print(f"🔧 Traitement du job : {pending_job_id} ({job['type']})")
            
            update_job_status(pending_job_id, "processing", progress=0)
            
            try:
                if job["type"] == "generate_video":
                    result_path = process_video_generation(job, pending_job_id)
                    jobs = load_jobs()
                    jobs[pending_job_id]["video_path"] = result_path
                    jobs[pending_job_id]["status"] = "completed"
                    jobs[pending_job_id]["progress"] = 100
                    save_jobs(jobs)
                    
                elif job["type"] == "upload_vodio":
                    process_upload(job, pending_job_id)
                    update_job_status(pending_job_id, "completed", progress=100)
                
                else:
                    raise ValueError(f"Type de job inconnu : {job['type']}")

                print(f"✅ Job {pending_job_id} terminé avec succès.")

            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"❌ Erreur sur le job {pending_job_id} : {e}")
                print(error_trace)
                update_job_status(pending_job_id, "failed", error_msg=str(e))
        
        else:
            time.sleep(2)

if __name__ == "__main__":
    main()
