import streamlit as st
import json
import os
import uuid

# --- OPTIONAL IMPORTS ---
try:
    from insta_generator import InstaGenerator
except ImportError:
    InstaGenerator = None

# On remplace l'uploader Insta par le notifieur Telegram
try:
    from telegram_notifier import TelegramNotifier
except ImportError:
    TelegramNotifier = None

# --- CONFIGURATION ---
INBOX_DIR = "inbox"
SECRETS_PATH = "/data/secrets.json"
if not os.path.exists("/data"):
    SECRETS_PATH = "secrets.json"

os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs("generated", exist_ok=True)

# --- UTILS ---
def load_secrets():
    """Load credentials from persistent JSON."""
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_secrets(data_dict):
    """Save credentials to persistent storage."""
    current = load_secrets()
    current.update(data_dict)
    
    with open(SECRETS_PATH, "w") as f:
        json.dump(current, f)
    st.toast("✅ Identifiants sauvegardés !", icon="💾")

# --- SIDEBAR (Config) ---
st.sidebar.title("🔐 Configuration")
secrets = load_secrets()

# VODIO CONFIG
with st.sidebar.expander("🎙️ Compte Vodio", expanded=not secrets.get("vodio_login")):
    vodio_login = st.text_input("Identifiant Vodio", value=secrets.get("vodio_login", ""))
    vodio_pass = st.text_input("Mot de passe Vodio", value=secrets.get("vodio_password", ""), type="password")

# TELEGRAM CONFIG (Remplacement d'Instagram)
with st.sidebar.expander("🔔 Notifications Telegram", expanded=False):
    tg_token = st.text_input("Bot Token", value=secrets.get("tg_token", ""))
    tg_chat_id = st.text_input("Chat ID", value=secrets.get("tg_chat_id", ""))

# GLOBAL SAVE BUTTON
if st.sidebar.button("Sauvegarder les accès"):
    save_secrets({
        "vodio_login": vodio_login,
        "vodio_password": vodio_pass,
        "tg_token": tg_token,
        "tg_chat_id": tg_chat_id
    })
    st.rerun()

# --- BLOCKING CHECK (Vodio Only) ---
if not secrets.get("vodio_login") or not secrets.get("vodio_password"):
    st.title("🎙️ Studio Oppodcast")
    st.warning("👋 Bienvenue ! Veuillez configurer vos accès Vodio dans le menu de gauche pour continuer.")
    st.stop()

# =========================================================
# MAIN APP
# =========================================================

st.title("🎙️ Studio Oppodcast")
st.caption(f"Connecté en tant que : {secrets['vodio_login']}")

# --- 1. UPLOAD FORM ---
with st.form("new_episode"):
    st.header("Nouvel Épisode")
    uploaded_file = st.file_uploader("Fichier Audio (MP3/WAV)", type=["mp3", "wav"])
    title = st.text_input("Titre de l'épisode")
    description = st.text_area("Description")
    
    submit_btn = st.form_submit_button("Mettre en file d'attente 🚀")

if submit_btn:
    if uploaded_file is not None and title:
        job_id = str(uuid.uuid4())
        mp3_filename = f"{job_id}.mp3"
        mp3_path = os.path.join(INBOX_DIR, mp3_filename)
        
        with open(mp3_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        job_data = {
            "id": job_id,
            "title": title,
            "description": description,
            "mp3_file": mp3_filename,
            "status": "pending",
            "created_at": str(os.path.getctime(mp3_path))
        }
        
        json_path = os.path.join(INBOX_DIR, f"{job_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, ensure_ascii=False, indent=4)
            
        st.success(f"✅ Épisode '{title}' ajouté à la file ! (ID: {job_id})")
        st.balloons()
    else:
        st.error("⚠️ Le fichier et le titre sont obligatoires !")

st.divider()

# --- 2. INSTAGRAM STUDIO ---
st.header("📸 Studio Instagram")
st.caption("Générer le post et l'envoyer sur mon téléphone.")

if not InstaGenerator:
    st.warning("⚠️ 'insta_generator.py' ou 'Pillow' manquant. Vérifiez les requirements.")
    st.stop()

col1, col2 = st.columns([1, 2])

if "generated_img_path" not in st.session_state:
    st.session_state["generated_img_path"] = None

with col1:
    insta_title = st.text_input("Titre du Post (ou laisser vide)", value="")
    insta_ep_num = st.text_input("Numéro Épisode", value="#01")
    generate_btn = st.button("Générer l'aperçu ✨")

with col2:
    final_title = insta_title if insta_title else title
    
    if generate_btn and final_title:
        try:
            gen = InstaGenerator()
            output_filename = f"insta_{uuid.uuid4()}.png"
            output_path = os.path.join("generated", output_filename)
            
            gen.generate_post(final_title, insta_ep_num, output_path)
            st.session_state["generated_img_path"] = output_path
            
        except Exception as e:
            st.error(f"Erreur de génération : {e}")

    if st.session_state["generated_img_path"] and os.path.exists(st.session_state["generated_img_path"]):
        img_path = st.session_state["generated_img_path"]
        st.image(img_path, caption="Aperçu Instagram", width=350)
        
        # Download
        with open(img_path, "rb") as file:
            st.download_button("Télécharger l'image 📥", data=file, file_name="insta_post.png", mime="image/png")
        
        st.divider()
        
        # --- TELEGRAM BUTTON ---
        if st.button("📲 Envoyer sur mon mobile (Telegram)"):
            secrets = load_secrets()
            if not secrets.get("tg_token") or not secrets.get("tg_chat_id"):
                st.error("⚠️ Configurez le Bot Telegram dans le menu de gauche !")
            elif not TelegramNotifier:
                st.error("⚠️ 'telegram_notifier.py' manquant.")
            else:
                with st.spinner("Envoi vers Telegram..."):
                    try:
                        notifier = TelegramNotifier(secrets["tg_token"], secrets["tg_chat_id"])
                        
                        # Construction du message prêt à copier
                        caption_text = (
                            f"🎙️ <b>{final_title}</b>\n\n"
                            f"Nouvel épisode disponible ! 🔥\n\n"
                            f"{description}\n\n"
                            f"#podcast #newepisode #{insta_ep_num.replace('#','')}"
                        )
                        
                        success = notifier.send_photo(img_path, caption_text)
                        
                        if success:
                            st.success("✅ Envoyé ! Vérifiez votre téléphone.")
                            st.balloons()
                        else:
                            st.error("❌ Échec de l'envoi Telegram.")
                    except Exception as e:
                        st.error(f"Erreur : {e}")
