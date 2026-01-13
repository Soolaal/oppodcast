from playwright.sync_api import sync_playwright
import time
import os

class VodioUploader:
    def __init__(self, headless=True):
        self.headless = headless

    def upload_episode(self, login, password, file_path, title, description):
        """
        Automates the upload process on Vodio using Playwright.
        """
        print(f"🔄 Connecting to Vodio as {login}...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=['--no-sandbox'])
            page = browser.new_page()
            
            try:
                # 1. Login
                page.goto("https://vodio.fr/login")
                page.fill('input[name="email"]', login)
                page.fill('input[name="password"]', password)
                page.click('button[type="submit"]')
                page.wait_for_url("**/dashboard", timeout=10000)
                
                # 2. Go to upload page
                page.goto("https://vodio.fr/podcasts/manage/upload")
                
                # 3. Upload File
                print("📤 Uploading MP3...")
                with page.expect_file_chooser() as fc_info:
                    page.click("text=Choisir un fichier")
                file_chooser = fc_info.value
                file_chooser.set_files(file_path)
                
                # Wait for upload completion (progress bar logic usually needed here)
                time.sleep(10) # Basic wait, improve if possible
                
                # 4. Fill Metadata
                print("📝 Filling metadata...")
                page.fill('input[name="title"]', title)
                page.fill('textarea[name="description"]', description)
                
                # 5. Submit
                page.click("text=Publier l'épisode")
                page.wait_for_load_state('networkidle')
                
                print("✅ Upload successful!")
                return True

            except Exception as e:
                print(f"❌ Error during upload: {e}")
                return False
            finally:
                browser.close()
