import time
import os
import logging
from playwright.sync_api import sync_playwright

# Configuration des logs pour voir ce qui se passe dans Docker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VodioUploader:
    def __init__(self, headless=True):
        """
        Initialisation simple sans login/password pour compatibilité avec le worker.
        """
        self.headless = headless

    def upload_episode(self, login, password, file_path, title, description):
        """
        Gère l'upload complet sur Vodio avec gestion des iframes imbriquées.
        Basé sur le script original fonctionnel.
        """
        # --- CONFIGURATION ---
        # ⚠️ REMPLACE "Test" PAR LE NOM EXACT DE TON PODCAST SUR VODIO
        PODCAST_NAME = "Test" 
        
        logging.info(f"🔄 [Vodio] Démarrage de la session pour {login}...")
        
        with sync_playwright() as p:
            # Lancement du navigateur avec options anti-crash pour Docker
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            page = browser.new_page()
            
            try:
                # --- 1. LOGIN ---
                logging.info("🔑 Connexion en cours...")
                page.goto("https://www.vodio.fr/moncompte/", timeout=60000)
                
                # Le login est dans une iframe spécifique
                frame = page.frame_locator("#moncompte")
                
                # Remplissage du formulaire
                frame.locator("#conn_login").click()
                frame.locator("#conn_login").fill(login)
                
                frame.locator("#conn_mypassword").click()
                frame.locator("#conn_mypassword").fill(password)
                
                time.sleep(1)
                
                # Validation du formulaire (gestion du click capricieux)
                try:
                    frame.locator("#connexion_valid").click(timeout=3000)
                except:
                    logging.warning("⚠️ Click standard échoué, tentative via dispatch_event...")
                    frame.locator("#connexion_valid").dispatch_event("click")
                
                # --- 2. NAVIGATION ---
                logging.info("🧭 Navigation vers le tableau de bord...")
                
                # Attente que le menu apparaisse (preuve de connexion)
                frame.get_by_role("button", name="Vos podcasts").wait_for(timeout=30000)
                frame.get_by_role("button", name="Vos podcasts").click()
                
                # Sélection du podcast spécifique
                logging.info(f"🎙️ Sélection du podcast : {PODCAST_NAME}")
                try:
                    frame.get_by_role("button", name=PODCAST_NAME).click()
                except Exception as e:
                    logging.error(f"❌ Impossible de trouver le podcast '{PODCAST_NAME}'. Vérifie le nom dans le script !")
                    raise e
                
                # Aller dans "Mes épisodes"
                frame.get_by_role("link", name="Mes épisodes").click()
                
                # --- 3. UPLOAD MP3 (IFRAME IMBRIQUÉE) ---
                logging.info(f"📤 Upload du fichier MP3 : {os.path.basename(file_path)}")
                
                # Ciblage de l'iframe d'upload à l'intérieur de l'iframe principale
                upload_frame = frame.frame_locator("#frameuploadmp3_1")
                
                # Envoi du fichier
                try:
                    upload_frame.get_by_role("button", name="Choose File").set_input_files(file_path)
                except:
                     logging.info("⚠️ Bouton standard non trouvé, utilisation du sélecteur générique input[type='file']")
                     upload_frame.locator("input[type='file']").set_input_files(file_path)
                
                # Validation de l'upload
                logging.info("📡 Envoi au serveur Vodio...")
                upload_frame.get_by_role("button", name="Uploader").click()
                
                # Attente fixe pour l'upload (ajuste selon la taille de tes fichiers et ta connexion)
                logging.info("⏳ Attente du transfert (20s)...")
                time.sleep(20) 
                
                # --- 4. MÉTADONNÉES ---
                logging.info("📝 Remplissage des métadonnées...")
                
                # Titre
                # On ré-assure le focus sur l'iframe principale
                frame.get_by_role("textbox", name="Titre de votre épisode").click()
                frame.get_by_role("textbox", name="Titre de votre épisode").fill(title)
                
                # Description
                frame.locator("#formaddepisode").get_by_role("textbox", name="Description").fill(description)
                
                # --- 5. PUBLICATION FINALE ---
                logging.info("🚀 Publication de l'épisode...")
                frame.get_by_role("button", name="Créer mon épisode").click()
                
                # Attente de confirmation visuelle ou technique
                logging.info("✅ En attente de la validation finale...")
                time.sleep(5)
                
                logging.info("🎉 ÉPISODE PUBLIÉ AVEC SUCCÈS !")
                return True

            except Exception as e:
                logging.error(f"❌ Erreur critique pendant l'upload : {e}")
                # Capture d'écran pour le debug
                try:
                    page.screenshot(path="failed_upload.png")
                    logging.info("📸 Capture d'écran de l'erreur sauvegardée : failed_upload.png")
                except:
                    pass
                return False
                
            finally:
                browser.close()
