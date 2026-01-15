import subprocess
import os
import re

class YouTubeGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_audio_duration(self, audio_path):
        """Récupère la durée de l'audio via ffprobe pour calculer la progression."""
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            audio_path
        ]
        try:
            return float(subprocess.check_output(cmd).decode().strip())
        except:
            return 0.0

    def generate_video(self, audio_path, image_path, output_filename="video.mp4", format="square", progress_callback=None):
        """
        Génère une vidéo optimisée (FFmpeg) avec callback de progression optionnel.
        
        Args:
            audio_path (str): Chemin fichier audio
            image_path (str): Chemin image
            output_filename (str): Nom fichier sortie
            format (str): 'square' ou 'landscape'
            progress_callback (func): Fonction(int) appelée avec le % de progression (0-100)
        """
        output_path = os.path.join(self.output_dir, output_filename)
        print(f"🌊 [V4.2] Génération FFmpeg : {output_filename}")

        # 0. Récupération durée pour la barre de chargement
        total_duration = self.get_audio_duration(audio_path)
        
        # --- 1. CONFIGURATION DU DESIGN ---
        if format == "square":
            W, H = 1080, 1080
            fg_size = 650
            wave_h = 250
            wave_y = "H-300"
        else:
            W, H = 1280, 720
            fg_size = 500
            wave_h = 150
            wave_y = "H-180"

        # --- 2. FILTRE COMPLEXE ---
        filter_complex = (
            f"[0:v]scale={int(W*1.2)}:{int(H*1.2)}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},"
            f"boxblur=20:2,"
            f"eq=brightness=-0.3"
            f"[bg];"
            
            f"[0:v]scale=-1:{fg_size}:force_original_aspect_ratio=decrease[fg];"
            
            f"[1:a]showwaves=s={W}x{wave_h}:mode=cline:colors=white@0.7[wave];"
            
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp1];"
            f"[comp1][wave]overlay=x=0:y={wave_y}:format=auto[outv]"
        )

        # --- 3. COMMANDE FFMPEG ---
        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-threads", "2",
            output_path
        ]

        # --- 4. EXÉCUTION AVEC PROGRESSION ---
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Lecture des logs en temps réel pour la barre
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        
        while True:
            # On lit stderr car ffmpeg écrit ses logs dedans
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                # Affiche le log brut dans la console (pour debug)
                print(line.strip()) 
                
                # Parsing pour la barre de progression
                if total_duration > 0 and progress_callback:
                    match = pattern.search(line)
                    if match:
                        h, m, s = map(float, match.groups())
                        current_time = h * 3600 + m * 60 + s
                        percent = min(int((current_time / total_duration) * 100), 99)
                        progress_callback(percent)

        if process.returncode != 0:
            print("❌ Erreur FFmpeg")
            if os.path.exists(output_path): os.remove(output_path)
            raise RuntimeError("FFmpeg a planté")

        # 100% à la fin
        if progress_callback: progress_callback(100)
        
        print(f"✅ Vidéo générée : {output_path}")
        return output_path
