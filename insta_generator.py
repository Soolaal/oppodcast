from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os

class InstaGenerator:
    def __init__(self, assets_dir="assets"):
        self.assets_dir = assets_dir
        os.makedirs(self.assets_dir, exist_ok=True)

    def get_available_fonts(self):
        fonts = [f for f in os.listdir(self.assets_dir) if f.endswith(".ttf")]
        if not fonts:
            return ["Default"]
        return fonts

    def generate_post(self, title, ep_number, output_path, 
                      bg_color="#1E1E1E", 
                      text_color="#FFFFFF",
                      accent_color="#FF4B4B",
                      font_name="Default",
                      font_size=60,
                      background_image_path=None,  # Renommé pour la clarté
                      darken_bg=True):             # Option pour assombrir le fond
        
        # 1. CRÉATION DU FOND
        if background_image_path and os.path.exists(background_image_path):
            try:
                # Charge l'image utilisateur comme fond
                img = Image.open(background_image_path).convert("RGB")
                
                # Optionnel : Redimensionner si l'image est énorme (> 1920px)
                # pour optimiser la perf et la taille fichier
                max_dim = 1350 # Standard Insta Portrait
                if max(img.size) > max_dim:
                    ratio = max_dim / max(img.size)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                width, height = img.size

                # Assombrir l'image pour que le texte ressorte
                if darken_bg:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(0.4) # 40% de luminosité
                    
            except Exception as e:
                print(f"Erreur Image de Fond: {e}, fallback couleur.")
                width, height = 1080, 1080
                img = Image.new('RGB', (width, height), color=bg_color)
        else:
            # Pas d'image = Fond Couleur Unie
            width, height = 1080, 1080
            img = Image.new('RGB', (width, height), color=bg_color)

        draw = ImageDraw.Draw(img)

        # 2. GESTION POLICE (Identique)
        selected_font_path = None
        if font_name != "Default":
            selected_font_path = os.path.join(self.assets_dir, font_name)

        try:
            if selected_font_path and os.path.exists(selected_font_path):
                font_title = ImageFont.truetype(selected_font_path, font_size)
                font_number = ImageFont.truetype(selected_font_path, int(font_size * 1.5))
            else:
                # Fallback Arial
                try:
                    font_title = ImageFont.truetype("arial.ttf", font_size)
                    font_number = ImageFont.truetype("arial.ttf", int(font_size * 1.5))
                except:
                    font_title = ImageFont.load_default()
                    font_number = ImageFont.load_default()
        except Exception:
            font_title = ImageFont.load_default()
            font_number = ImageFont.load_default()

        # 3. TEXTE
        
        # Numéro (Haut)
        y_header = int(height * 0.15)
        draw.text((width/2, y_header), ep_number, font=font_number, fill=accent_color, anchor="mm")

        # Titre (Centré Multi-lignes)
        lines = []
        words = title.split()
        current_line = []
        margin = int(width * 0.15) # Marges plus larges (15%)
        max_width = width - (margin * 2)

        for word in words:
            current_line.append(word)
            line_width = draw.textlength(" ".join(current_line), font=font_title)
            if line_width > max_width: 
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))

        total_text_height = len(lines) * (font_size * 1.3)
        start_y = (height / 2) - (total_text_height / 2)
        y_text = start_y
        
        # Ombre portée toujours active sur fond image
        has_shadow = True if background_image_path else False
        
        for line in lines:
            if has_shadow:
                # Ombre noire forte pour lisibilité
                draw.text((width/2 + 4, y_text + 4), line, font=font_title, fill="black", anchor="mm")
            
            draw.text((width/2, y_text), line, font=font_title, fill=text_color, anchor="mm")
            y_text += font_size * 1.3

        img.save(output_path)
        return output_path
