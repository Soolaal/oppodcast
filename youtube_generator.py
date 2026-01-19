import subprocess
import os
import re

class YouTubeGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_audio_duration(self, audio_path):
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        try: return float(subprocess.check_output(cmd).decode().strip())
        except: return 0.0

    def generate_video(self, audio_path, image_path, output_filename="video.mp4", format="square", progress_callback=None, render_mode="balanced", bg_color="#000000"):
        """
        render_mode: 'turbo' (couleur), 'balanced' (fake blur), 'quality' (boxblur)
        """
        output_path = os.path.join(self.output_dir, output_filename)
        total_duration = self.get_audio_duration(audio_path)
        print(f"🌊 [YouTube {render_mode.upper()}] Génération : {output_filename}")

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

        # --- CONSTRUCTION DU FOND SELON LE MODE ---
        bg_filter = ""
        
        if render_mode == "turbo":
            # Fond Couleur Unie (Zéro CPU)
            # On génère une source couleur 'color'
            bg_filter = (
                f"color=c={bg_color}:s={W}x{H}:d={total_duration}[bg];"
            )
            # Pas besoin de l'input [0] pour le fond, on l'utilise direct pour le premier plan
            fg_input = "[0:v]"
        
        elif render_mode == "balanced":
            # Fond Scale Down/Up (Rapide)
            bg_filter = (
                f"[0:v]scale=50:-1:force_original_aspect_ratio=increase[low];"
                f"[low]scale={W}:{H},setsar=1,eq=brightness=-0.3[bg];"
            )
            fg_input = "[0:v]"

        else: # quality
            # Fond BoxBlur (Lent)
            bg_filter = (
                f"[0:v]scale={int(W*1.2)}:{int(H*1.2)}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},boxblur=20:2,eq=brightness=-0.3[bg];"
            )
            fg_input = "[0:v]"

        # --- RESTE DU FILTRE ---
        filter_complex = (
            bg_filter +
            f"{fg_input}scale=-1:{fg_size}:force_original_aspect_ratio=decrease[fg];"
            f"[1:a]showwaves=s={W}x{wave_h}:mode=cline:colors=white@0.7[wave];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp1];"
            f"[comp1][wave]overlay=x=0:y={wave_y}:format=auto[outv]"
        )

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-pix_fmt", "yuv420p", "-threads", "2",
            output_path
        ]

        # Execution + Progress (inchangé)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None: break
            if line and total_duration > 0 and progress_callback:
                print(line.strip())
                match = pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    curr = h*3600 + m*60 + s
                    progress_callback(min(int((curr/total_duration)*100), 99))
        
        if process.returncode != 0: raise RuntimeError("FFmpeg Error")
        if progress_callback: progress_callback(100)
        return output_path
