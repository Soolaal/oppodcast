from PIL import Image, ImageDraw, ImageFont
import os

class InstaGenerator:
    def __init__(self, assets_dir="assets"):
        self.assets_dir = assets_dir
        os.makedirs(self.assets_dir, exist_ok=True)

    def get_available_fonts(self):
        return [f for f in os.listdir(self.assets_dir) if f.lower().endswith(".ttf")]

    def generate_post(self, title, ep_number, output_path, bg_color="#1E1E1E", text_color="#FFFFFF", accent_color="#FF4B4B", font_name=None, font_size=70, template_path=None):
        
        # 1. Determine Output Size & Base Image
        if template_path and os.path.exists(template_path):
            try:
                # Use the template AS IS (Respect original dimensions)
                img = Image.open(template_path).convert("RGBA")
                W, H = img.size
            except Exception as e:
                print(f"Error loading template: {e}")
                # Fallback to square if loading fails
                W, H = 1080, 1080
                img = Image.new("RGBA", (W, H), color=bg_color)
        else:
            # No template = Default Square
            W, H = 1080, 1080
            img = Image.new("RGBA", (W, H), color=bg_color)
        
        draw = ImageDraw.Draw(img)
        
        # 2. Font Loading
        font_title = None
        font_ep = None
        
        if font_name:
            font_path = os.path.join(self.assets_dir, font_name)
            if os.path.exists(font_path):
                try:
                    font_title = ImageFont.truetype(font_path, int(font_size))
                    font_ep = ImageFont.truetype(font_path, int(font_size * 1.5))
                except:
                    pass

        if font_title is None:
            font_title = ImageFont.load_default()
            font_ep = ImageFont.load_default()

        # 3. Draw Text
        if ep_number:
            draw.text((W/2, H/3), ep_number, font=font_ep, fill=accent_color, anchor="mm")
        
        if title:
            draw.text((W/2, H/2), title, font=font_title, fill=text_color, anchor="mm", align="center")

        # 4. Save
        img.save(output_path)
        return output_path
