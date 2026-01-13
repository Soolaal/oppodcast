from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, ColorClip
import os
import PIL.Image

# Fix for older Pillow versions
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

class YouTubeGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_video(self, audio_path, image_path, output_filename="video.mp4", format="square"):
        print(f"🎬 Generating video ({format}): {output_filename}...")
        
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # --- LAYOUT CONFIG ---
            if format == "square":
                W, H = 1080, 1080
                fg_size = 650 # Dezoom 60%
            else:
                W, H = 1920, 1080
                fg_size = 850

            # 1. Background (Blurred/Darkened)
            bg_clip = (ImageClip(image_path)
                       .set_duration(duration)
                       .resize(height=H*1.2) # Zoom in
                       .set_position("center")
                       .set_opacity(0.15)) # Dark

            black_bg = ColorClip(size=(W, H), color=(0,0,0)).set_duration(duration)

            # 2. Foreground (Sharp)
            fg_clip = (ImageClip(image_path)
                       .set_duration(duration)
                       .resize(height=fg_size)
                       .set_position("center"))

            # Compose
            final = CompositeVideoClip([black_bg, bg_clip, fg_clip])
            final = final.set_audio(audio_clip)

            output_path = os.path.join(self.output_dir, output_filename)
            final.write_videofile(output_path, fps=1, codec="libx264", audio_codec="aac")
            
            return output_path

        except Exception as e:
            print(f"❌ Video Generation Error: {e}")
            raise e
