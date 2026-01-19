import subprocess
import os
import re

class ShortsGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_short(self, audio_path, image_path, start_time=0, duration=58, output_filename="short.mp4", progress_callback=None, render_mode="balanced", bg_color="#000000"):
        output_path = os.path.join(self.output_dir, output_filename)
        print(f"📱 [Shorts {render_mode.upper()}] Génération PC : {output_filename}")
        
        # Format vertical strict pour Shorts/Reels/TikTok
        W, H = 1080, 1920

        # --- FOND ---
        bg_filter = ""
        fg_input = "[0:v]"
        
        if render_mode == "turbo":
            # Fond couleur unie
            bg_filter = f"color=c={bg_color}:s={W}x{H}:d={duration}[bg];"
            fg_input = "[0:v]"
            
        elif render_mode == "balanced":
            # Flou Gaussien Standard
            bg_filter = (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"gblur=sigma=20:steps=2,eq=brightness=-0.4[bg];"
            )
            fg_input = "[0:v]"
            
        else: # quality
            # Zoom lent vertical + Flou Gaussien plus fort
            # On zoom légèrement (1.2x) pour donner du mouvement au fond statique
            bg_filter = (
                f"[0:v]scale=-1:{int(H*1.2)},zoompan=z='min(zoom+0.0003,1.3)':d={duration*25}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H},"
                f"gblur=sigma=30:steps=3,eq=brightness=-0.5[bg];"
            )
            fg_input = "[0:v]"

        # --- FILTRE COMPLEXE ---
        # Note: [1:a] est l'audio découpé par l'argument -ss/-t de l'input
        filter_complex = (
            bg_filter +
            f"{fg_input}scale={W}:-1:force_original_aspect_ratio=decrease[fg];"
            f"[1:a]showwaves=s={W}x350:mode=cline:colors=white@0.9:rate=25[wave];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp1];"
            f"[comp1][wave]overlay=x=0:y=H-450:format=auto[outv]"
        )

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-ss", str(start_time), "-t", str(duration), "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "1:a",
            
            # --- PARAMÈTRES PC (Qualité) ---
            "-c:v", "libx264", 
            "-preset", "medium",   # Plus propre que ultrafast
            "-crf", "23",          # Qualité constante
            "-tune", "stillimage",
            
            "-c:a", "aac", "-b:a", "192k", # Audio propre
            
            "-pix_fmt", "yuv420p",
            # Pas de restriction de threads sur PC
            
            "-t", str(duration),
            output_path
        ]
        
        # Execution
        print(f"Commande : {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None: break
            if line:
                print(line.strip())
                if duration > 0 and progress_callback:
                    match = pattern.search(line)
                    if match:
                        h, m, s = map(float, match.groups())
                        curr = h*3600 + m*60 + s
                        progress_callback(min(int((curr/duration)*100), 99))
        
        if process.returncode != 0: raise RuntimeError("FFmpeg Error")
        if progress_callback: progress_callback(100)
        return output_path
