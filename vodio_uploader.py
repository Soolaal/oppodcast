import time
from playwright.sync_api import sync_playwright

class VodioUploader:
    def __init__(self, login, password, headless=True):
        self.login = login
        self.password = password
        self.headless = headless

    def upload(self, mp3_path, title, description, image_path=None):
        """
        Handles full upload process including nested iframes.
        """
        PODCAST_NAME = "Test"  # <--- REPLACE WITH YOUR EXACT PODCAST NAME ON VODIO
        
        print(f"[Vodio] Connecting with {self.login}...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            # --- 1. LOGIN ---
            page.goto("https://www.vodio.fr/moncompte/")
            frame = page.frame_locator("#moncompte")
            
            print("Logging in...")
            frame.locator("#conn_login").click()
            frame.locator("#conn_login").type(self.login, delay=50)
            frame.locator("#conn_mypassword").click()
            frame.locator("#conn_mypassword").type(self.password, delay=50)
            time.sleep(1)
            
            try:
                frame.locator("#connexion_valid").click(timeout=2000)
            except:
                frame.locator("#connexion_valid").dispatch_event("click")
            
            # --- 2. NAVIGATION ---
            print("Navigating to podcast dashboard...")
            # Wait for menu to appear after login
            frame.get_by_role("button", name="Vos podcasts").wait_for()
            frame.get_by_role("button", name="Vos podcasts").click()
            
            # Select specific Podcast
            print(f"Selecting podcast: {PODCAST_NAME}")
            frame.get_by_role("button", name=PODCAST_NAME).click()
            
            # Go to "My episodes"
            frame.get_by_role("link", name="Mes épisodes").click()
            
            # --- 3. UPLOAD MP3 (NESTED IFRAME) ---
            print(f"Uploading MP3: {mp3_path}")
            
            # Target the upload iframe inside the main iframe
            upload_frame = frame.frame_locator("#frameuploadmp3_1")
            
            # Handle file input (Vodio specific behavior)
            try:
                upload_frame.get_by_role("button", name="Choose File").set_input_files(mp3_path)
            except:
                 # Fallback if button changes
                 upload_frame.locator("input[type='file']").set_input_files(mp3_path)
            
            # Validate MP3 upload
            print("Sending MP3 to server...")
            upload_frame.get_by_role("button", name="Uploader").click()
            
            # Wait for upload completion (adjust based on network speed)
            time.sleep(10) 
            
            # --- 4. METADATA ---
            print("Filling metadata...")
            
            # Title
            frame.get_by_role("textbox", name="Titre de votre épisode").click()
            frame.get_by_role("textbox", name="Titre de votre épisode").fill(title)
            
            # Description
            frame.locator("#formaddepisode").get_by_role("textbox", name="Description").fill(description)
            
            # --- 5. COVER IMAGE (Optional) ---
            if image_path:
                print(f"Uploading Cover: {image_path}")
                # Image button is in the main frame
                frame.get_by_role("button", name="Choose File").set_input_files(image_path)
                frame.get_by_role("button", name="Valider").click()
                time.sleep(2)

            # --- 6. FINAL PUBLICATION ---
            print("Publishing...")
            frame.get_by_role("button", name="Créer mon épisode").click()
            
            # Wait for confirmation
            print("Waiting for confirmation...")
            time.sleep(5)
            
            print("EPISODE PUBLISHED!")
            browser.close()
            return True
