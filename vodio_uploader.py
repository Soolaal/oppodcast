import time
import os
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VodioUploader:
    def __init__(self, headless=True):
        """
        Simple initialization without login/password for worker compatibility.
        """
        self.headless = headless

    def upload_episode(self, login, password, file_path, title, description):
        """
        Handles complete upload to Vodio with nested iframe management.
        Based on the original functional script.
        """
        # --- CONFIGURATION ---
        PODCAST_NAME = "Test"  # TODO: Change this to your actual podcast name on Vodio
        
        logging.info(f"[Vodio] Starting session for {login}...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            page = browser.new_page()
            
            try:
                # --- 1. LOGIN ---
                logging.info("Logging in...")
                page.goto("https://www.vodio.fr/moncompte/", timeout=60000)
                
                # Locate the main account frame
                frame = page.frame_locator("#moncompte")
               
                frame.locator("#conn_login").click()
                frame.locator("#conn_login").fill(login)
                
                frame.locator("#conn_mypassword").click()
                frame.locator("#conn_mypassword").fill(password)
                
                time.sleep(1)
                
                try:
                    frame.locator("#connexion_valid").click(timeout=3000)
                except:
                    logging.warning("Standard click failed, attempting via dispatch_event...")
                    frame.locator("#connexion_valid").dispatch_event("click")
                
                # --- 2. NAVIGATION ---
                logging.info("Navigating to dashboard...")
                
                # Selectors kept in French as they must match the website UI
                frame.get_by_role("button", name="Vos podcasts").wait_for(timeout=30000)
                frame.get_by_role("button", name="Vos podcasts").click()
                
                logging.info(f"Selecting podcast: {PODCAST_NAME}")
                try:
                    frame.get_by_role("button", name=PODCAST_NAME).click()
                except Exception as e:
                    logging.error(f"Could not find podcast '{PODCAST_NAME}'. Check the name in the script!")
                    raise e
                
                frame.get_by_role("link", name="Mes épisodes").click()
                
                # --- 3. UPLOAD MP3 (NESTED IFRAME) ---
                logging.info(f"Uploading MP3 file: {os.path.basename(file_path)}")
                
                # Locate the upload iframe
                upload_frame = frame.frame_locator("#frameuploadmp3_1")
                
                try:
                    upload_frame.get_by_role("button", name="Choose File").set_input_files(file_path)
                except:
                     logging.info("Standard button not found, using generic input[type='file'] selector")
                     upload_frame.locator("input[type='file']").set_input_files(file_path)
                
                logging.info("Sending to Vodio server...")
                upload_frame.get_by_role("button", name="Uploader").click()
                
                logging.info("Waiting for transfer (20s)...")
                time.sleep(20) 
                
                # --- 4. METADATA ---
                logging.info("Filling metadata...")

                frame.get_by_role("textbox", name="Titre de votre épisode").click()
                frame.get_by_role("textbox", name="Titre de votre épisode").fill(title)
                
                frame.locator("#formaddepisode").get_by_role("textbox", name="Description").fill(description)

                logging.info("Publishing episode...")
                frame.get_by_role("button", name="Créer mon épisode").click()
                
                logging.info("Waiting for final validation...")
                time.sleep(5)
                
                logging.info("Episode published sucessfully")
                return True

            except Exception as e:
                logging.error(f"Critical error during upload: {e}")

                try:
                    page.screenshot(path="failed_upload.png")
                    logging.info("Error screenshot saved: failed_upload.png")
                except:
                    pass
                return False
                
            finally:
                browser.close()
