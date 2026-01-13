from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, ColorClip
import os
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

class YouTubeGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_video(self, audio_path, image_path, output_filename="video.mp4", format="square"):
        """
        Génère une vidéo avec effet de profondeur (Fond flou/sombre + Image nette).
        """
        print(f"🎬 Génération vidéo ({format}) : {output_filename}...")
        
        try:
            # 1. Charger l'audio
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # --- CONFIGURATION DES TAILLES ---
            if format == "square":
                W, H = 1080, 1080
                # ON DEZOOME LE PREMIER PLAN (Demande utilisateur : 60% environ)
                # 60% de 1080px = 648px. On arrondit à 650px.
                fg_size = 650 
            else:
                # Mode Paysage (16:9)
                W, H = 1920, 1080
                fg_size = 850

            # 2. CRÉATION DU FOND (Background)
            # On garde le fond bien rempli (zoom 120%)
            bg_clip = (ImageClip(image_path)
                       .set_duration(duration)
                       .resize(height=H*1.2)
                       .set_position("center"))
            
            # Opacité du fond (30%)
            bg_clip = bg_clip.set_opacity(0.20)

            # Fond noir solide derrière
            black_bg = ColorClip(size=(W, H), color=(10,10,10)).set_duration(duration)

            # 3. CRÉATION DU PREMIER PLAN (Foreground)
            if format == "square":
                 foreground = (ImageClip(image_path)
                              .set_duration(duration)
                              .resize(width=fg_size) # 650px de large
                              .set_position("center"))
            else:
                 foreground = (ImageClip(image_path)
                              .set_duration(duration)
                              .resize(height=fg_size)
                              .set_position("center"))

            # 4. COMPOSITION
            video = CompositeVideoClip(
                [black_bg, bg_clip, foreground], 
                size=(W, H)
            )
            
            video = video.set_audio(audio_clip)
            
            # 5. EXPORT
            output_path = os.path.join(self.output_dir, output_filename)
            
            video.write_videofile(
                output_path, 
                fps=1,
                codec="libx264", 
                audio_codec="aac",
                preset="ultrafast",
                threads=4
            )
            
            print(f"✅ Vidéo générée : {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Erreur : {e}")
            raise e
