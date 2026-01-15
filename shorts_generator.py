import subprocess
import os
import re

class ShortsGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_short(self, audio_path, image_path, start_time=0, duration=58, output_filename="short.mp4", progress_callback=None):
        """
        Génère un Short Vertical (9:16) optimisé FFmpeg.
        
        Args:
            audio_path (str): Fichier audio source
            image_path (str): Image source
            start_time (int): Début de l'extrait en secondes
            duration (int): Durée de l'extrait (max 60s pour Shorts)
            output_filename (str): Nom du fichier de sortie
            progress_callback (func): Fonction pour mise à jour barre (0-100)
        """
        output_path = os.path.join(self.output_dir, output_filename)
        print(f"📱 [Shorts V4] Génération : {output_filename} ({duration}s)")

        # Dimensions Verticales (1080x1920)
        W, H = 1080, 1920
        
        # --- FILTRE COMPLEXE ---
        # 1. Fond flou zoomé pour remplir le vertical
        # 2. Image au centre
        # 3. Waveform en bas
        filter_complex = (
            # Fond : On prend l'image, on scale pour couvrir la hauteur 1920, on crop 1080x1920
            f"[0:v]scale=-1:{int(H*1.2)}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},"
            f"boxblur=40:5,"        # Flou plus fort pour le short
            f"eq=brightness=-0.4"   # Plus sombre
            f"[bg];"
            
            # Premier plan : Image carrée 1080x1080 au centre
            f"[0:v]scale={W}:-1:force_original_aspect_ratio=decrease[fg];"
            
            # Waveform : En bas
            f"[0:a]showwaves=s={W}x300:mode=cline:colors=white@0.8[wave];"
            
            # Composition
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp1];"
            f"[comp1][wave]overlay=x=0:y=H-400:format=auto[outv]"
        )

        # --- COMMANDE FFMPEG ---
        cmd = [
            "ffmpeg",
            "-y",                   # Force l'écrasement
            "-loop", "1",           # Image en boucle
            "-i", image_path,       # Input 0
            "-ss", str(start_time), # Début de l'extrait audio
            "-t", str(duration),    # Durée de lecture audio
            "-i", audio_path,       # Input 1
            "-filter_complex", 
            filter_complex.replace("[0:a]", "[1:a]"), 
            
            "-map", "[outv]",
            "-map", "1:a",
            
            # --- OPTIONS D'ENCODAGE ---
            "-c:v", "libx264",
            "-preset", "ultrafast", # Indispensable pour l'Orange Pi
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-threads", "2",        # Sécurité CPU
            
            # --- SECURITÉ STOP ---
            "-t", str(duration),    # Force l'arrêt global à la durée voulue
            output_path
        ]

        print(f"🛠️ Commande : {' '.join(cmd)}")

        # --- EXÉCUTION AVEC BARRE DE PROGRESSION ---
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Lecture des logs
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        
        # On itère sur stderr ligne par ligne
        for line in process.stderr:
            # DEBUG : Affiche ce que fait FFmpeg dans ta console
            print(line.strip()) 
            
            if duration > 0 and progress_callback:
                match = pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    percent = min(int((current_time / duration) * 100), 99)
                    progress_callback(percent)

        # Attente explicite de la fin du processus
        process.wait()

        if process.returncode != 0:
            print(f"❌ Erreur FFmpeg (Code {process.returncode})")
            if os.path.exists(output_path): os.remove(output_path)
            raise RuntimeError("FFmpeg Short a planté (voir logs ci-dessus)")

        # Si on est là, c'est fini proprement
        if progress_callback: progress_callback(100)
        print(f"✅ Short généré avec succès : {output_path}")
        return output_path
