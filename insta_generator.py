from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

class InstaGenerator:
    def __init__(self, template_path="assets/template_insta.png", font_path="assets/font.ttf"):
        self.template_path = template_path
        self.font_path = font_path
        # Création des dossiers si besoin
        os.makedirs("assets", exist_ok=True)
        os.makedirs("generated", exist_ok=True)

    def generate_post(self, title, episode_number, output_path):
        """
        Génère une image 1080x1080 pour Instagram.
        """
        # 1. Charger le template (ou créer un fond noir si absent)
        try:
            img = Image.open(self.template_path).convert("RGBA")
            img = img.resize((1080, 1080))
        except FileNotFoundError:
            print("⚠️ Template non trouvé, utilisation d'un fond uni.")
            img = Image.new('RGBA', (1080, 1080), color='#1E1E1E')

        draw = ImageDraw.Draw(img)

        # 2. Charger la police (ou default si absente)
        try:
            # Taille 60 pour le titre, 40 pour le sous-titre
            title_font = ImageFont.truetype(self.font_path, 80)
            subtitle_font = ImageFont.truetype(self.font_path, 50)
        except IOError:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # 3. Écrire le Numéro d'épisode (En haut au centre ou selon ton design)
        episode_text = f"ÉPISODE #{episode_number}"
        draw.text((540, 300), episode_text, font=subtitle_font, fill="#FF4B4B", anchor="mm")

        # 4. Écrire le Titre (Centré avec retour à la ligne automatique)
        # On wrap le texte pour qu'il ne sorte pas de l'image
        lines = textwrap.wrap(title, width=20) # Ajuster la width selon la police
        y_text = 540 # Centre vertical
        
        for line in lines:
            # Calculer la taille de la ligne pour bien centrer
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            draw.text(((1080 - text_width) / 2, y_text), line, font=title_font, fill="white")
            y_text += text_height + 20 # Espacement entre les lignes

        # 5. Sauvegarder
        img.save(output_path)
        return output_path

# Test rapide si lancé direct
if __name__ == "__main__":
    gen = InstaGenerator()
    gen.generate_post("Comment automatiser son Podcast avec Python ?", "42", "test_insta.png")
