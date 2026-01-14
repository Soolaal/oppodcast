from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, ColorClip, TextClip
import os

class ShortsGenerator:
    def __init__(self, output_dir="generated"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_short(self, audio_path, image_path, start_time, duration, output_filename="short.mp4", title_text=None):
        print(f"📱 Génération Short : {output_filename} (Début: {start_time}s, Durée: {duration}s)")
        
        try:
            # 1. Charger et couper l'audio
            full_audio = AudioFileClip(audio_path)
            
            # Sécurité si l'extrait dépasse la fin
            if start_time + duration > full_audio.duration:
                duration = full_audio.duration - start_time
            
            short_audio = full_audio.subclip(start_time, start_time + duration)
            
            # 2. Config Vidéo Verticale (9:16 -> 1080x1920)
            W, H = 1080, 1920
            
            # Fond flou (l'image étirée et floutée)
            bg_clip = (ImageClip(image_path)
                       .set_duration(duration)
                       .resize(height=H)
                       .crop(x1=0, y1=0, width=W, height=H, x_center=W/2, y_center=H/2) # Crop central
                       .set_position("center"))
            
            # Assombrir le fond
            bg_clip = bg_clip.set_opacity(0.4)
            black_bg = ColorClip(size=(W, H), color=(10,10,10)).set_duration(duration)

            # Image principale (carrée au centre)
            # On la garde nette, largeur = 80% de l'écran
            fg_width = int(W * 0.85)
            fg_clip = (ImageClip(image_path)
                       .set_duration(duration)
                       .resize(width=fg_width)
                       .set_position(("center", "center")))
            
            clips = [black_bg, bg_clip, fg_clip]

            # (Optionnel) Ajouter un titre en haut si fourni
            # Note: TextClip nécessite ImageMagick. On le commente par sécurité si pas installé.
            # if title_text:
            #     txt_clip = (TextClip(title_text, fontsize=70, color='white', font='Arial-Bold')
            #                 .set_position(('center', 200))
            #                 .set_duration(duration))
            #     clips.append(txt_clip)

            # 3. Composition
            video = CompositeVideoClip(clips, size=(W, H))
            video = video.set_audio(short_audio)
            
            # 4. Export
            output_path = os.path.join(self.output_dir, output_filename)
            video.write_videofile(
                output_path, 
                fps=24, # 24fps suffit pour des shorts statiques
                codec="libx264", 
                audio_codec="aac",
                preset="fast",
                threads=4
            )
            
            return output_path
            
        except Exception as e:
            print(f"Erreur Short : {e}")
            raise e
