import subprocess
import os
import re

class ShortsGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_short(self, audio_path, image_path, start_time=0, duration=58, output_filename="short.mp4", progress_callback=None, render_mode="balanced", bg_color="#000000"):
        output_path = os.path.join(self.output_dir, output_filename)
        print(f"📱 [Shorts {render_mode.upper()}] Génération : {output_filename}")
        W, H = 1080, 1920

        # --- FOND ---
        bg_filter = ""
        if render_mode == "turbo":
            bg_filter = f"color=c={bg_color}:s={W}x{H}:d={duration}[bg];"
            fg_input = "[0:v]"
        elif render_mode == "balanced":
            bg_filter = (
                f"[0:v]scale=50:-1:force_original_aspect_ratio=increase[low];"
                f"[low]scale={W}:{H},setsar=1,eq=brightness=-0.4[bg];"
            )
            fg_input = "[0:v]"
        else: # quality
            bg_filter = (
                f"[0:v]scale=-1:{int(H*1.2)}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},boxblur=40:5,eq=brightness=-0.4[bg];"
            )
            fg_input = "[0:v]"

        filter_complex = (
            bg_filter +
            f"{fg_input}scale={W}:-1:force_original_aspect_ratio=decrease[fg];"
            f"[1:a]showwaves=s={W}x300:mode=cline:colors=white@0.8[wave];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp1];"
            f"[comp1][wave]overlay=x=0:y=H-400:format=auto[outv]"
        )

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-ss", str(start_time), "-t", str(duration), "-i", audio_path,
            "-filter_complex", filter_complex.replace("[0:a]", "[1:a]"),
            "-map", "[outv]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", "-threads", "2",
            "-t", str(duration),
            output_path
        ]
        
        # Execution (même logique que d'habitude)
        print(f"🛠️ Commande : {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        for line in process.stderr:
            print(line.strip())
            if duration > 0 and progress_callback:
                match = pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    curr = h*3600 + m*60 + s
                    progress_callback(min(int((curr/duration)*100), 99))
        
        process.wait()
        if process.returncode != 0: raise RuntimeError("FFmpeg Error")
        if progress_callback: progress_callback(100)
        return output_path
