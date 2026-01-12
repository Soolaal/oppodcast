import requests
import os

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{token}"

    def send_photo(self, photo_path, caption):
        """
        Send photo with HTML caption.
        """
        url = f"{self.api_url}/sendPhoto"
        try:
            with open(photo_path, "rb") as f:
                payload = {
                    "chat_id": self.chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                files = {"photo": f}
                
                resp = requests.post(url, data=payload, files=files)
                
                if not resp.ok:
                    print(f"Telegram Error: {resp.text}")
                
                return resp.ok
        except Exception as e:
            print(f"Telegram Exception: {e}")
            return False
