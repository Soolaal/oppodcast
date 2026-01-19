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
        render_mode: 
          - 'turbo': Fond couleur unie (Rapide)
          - 'balanced': Flou léger optimisé (Standard)
          - 'quality': Flou artistique + Zoom lent (Lent)
        """
        output_path = os.path.join(self.output_dir, output_filename)
        total_duration = self.get_audio_duration(audio_path)
        print(f"[YouTube {render_mode.upper()}] Génération PC : {output_filename}")

        if format == "square":
            W, H = 1080, 1080
            fg_size = 750
            wave_h = 280
            wave_y = "H-320"
        else:
            W, H = 1920, 1080 
            fg_size = 700
            wave_h = 250
            wave_y = "H-250"

        bg_filter = ""
        fg_input = "[0:v]" 
        
        if render_mode == "turbo":

            bg_filter = (
                f"color=c={bg_color}:s={W}x{H}:d={total_duration}[bg];"
            )

            fg_input = "[0:v]"
        
        elif render_mode == "balanced":

            bg_filter = (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"gblur=sigma=20:steps=2,eq=brightness=-0.3[bg];"
            )
            fg_input = "[0:v]"

        else:
            bg_filter = (
                f"[0:v]scale=8000:-1,zoompan=z='min(zoom+0.0002,1.2)':d={total_duration*25}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H},"
                f"gblur=sigma=30:steps=3,eq=brightness=-0.4[bg];"
            )
            fg_input = "[0:v]"

        filter_complex = (
            bg_filter +
            f"{fg_input}scale=-1:{fg_size}:force_original_aspect_ratio=decrease[fg];"
            f"[1:a]showwaves=s={W}x{wave_h}:mode=cline:colors=white@0.8:rate=25[wave];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[comp1];"
            f"[comp1][wave]overlay=x=0:y={wave_y}:format=auto[outv]"
        )

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "1:a",
            
            "-c:v", "libx264", 
            "-preset", "medium", 
            "-crf", "23", 
            "-tune", "stillimage", 
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-pix_fmt", "yuv420p",
            output_path
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None: break
            if line:
                print(line.strip())
                if total_duration > 0 and progress_callback:
                    match = pattern.search(line)
                    if match:
                        h, m, s = map(float, match.groups())
                        curr = h*3600 + m*60 + s
                        progress_callback(min(int((curr/total_duration)*100), 99))
        
        if process.returncode != 0: raise RuntimeError("FFmpeg Error")
        if progress_callback: progress_callback(100)
        return output_path
