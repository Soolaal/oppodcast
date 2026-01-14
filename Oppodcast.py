import streamlit as st
import json
import os
import uuid
import time

# --- 1. CONFIGURATION DE LA PAGE (DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT) ---
st.set_page_config(
    page_title="Oppodcast Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ (Pour un look plus "App") ---
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    h1 {color: #FF4B4B;} 
    .stButton button {width: 100%; border-radius: 8px;}
    div[data-testid="stExpander"] {border: 1px solid #333; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)


# --- IMPORTS OPTIONNELS ---
try:
    from insta_generator import InstaGenerator
except ImportError:
    InstaGenerator = None
try:
    from telegram_notifier import TelegramNotifier
except ImportError:
    TelegramNotifier = None
try:
    from youtube_generator import YouTubeGenerator
except ImportError:
    YouTubeGenerator = None
try:
    from youtube_uploader import YouTubeUploader
except ImportError:
    YouTubeUploader = None

# --- GESTION DES CHEMINS (Compatible Home Assistant / Local) ---
if os.path.exists("/share"):
    BASE_DIR = "/share/oppodcast"
else:
    BASE_DIR = os.getcwd()

INBOX_DIR = os.path.join(BASE_DIR, "inbox")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SECRETS_PATH = os.path.join(BASE_DIR, "secrets.json")

os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# --- FONCTIONS UTILITAIRES ---
def load_secrets():
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_secrets(data_dict):
    current = load_secrets()
    current.update(data_dict)
    with open(SECRETS_PATH, "w") as f:
        json.dump(current, f)
    st.toast("Identifiants sauvegardés !", icon="💾")

def get_episode_label(filename):
    json_name = filename.replace(".mp3", ".json")
    json_path = os.path.join(INBOX_DIR, json_name)
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            real_title = data.get("title", "Sans titre")
            return f"🎙️ {real_title}"
        except:
            pass
    return f"📁 {filename}"

# --- SESSION STATE ---
if "generated_video_path" not in st.session_state:
    st.session_state["generated_video_path"] = None
if "generated_img_path" not in st.session_state:
    st.session_state["generated_img_path"] = None
if "video_mp3_source" not in st.session_state:
    st.session_state["video_mp3_source"] = None

# =========================================================
# BARRE LATÉRALE (SIDEBAR) - DESIGN AMÉLIORÉ
# =========================================================
secrets = load_secrets()

# Logo (Si fichier présent)
logo_path = os.path.join(ASSETS_DIR, "logo.png")
if os.path.exists(logo_path):
    st.logo(logo_path, icon_image=logo_path)
    st.sidebar.image(logo_path, width=200)

st.sidebar.header("Paramètres")

with st.sidebar.expander("Compte Vodio", expanded=not secrets.get("vodio_login")):
    vodio_login = st.text_input("Identifiant", value=secrets.get("vodio_login", ""))
    vodio_pass = st.text_input("Mot de passe", value=secrets.get("vodio_password", ""), type="password")

with st.sidebar.expander("Telegram Bot", expanded=False):
    tg_token = st.text_input("Bot Token", value=secrets.get("tg_token", ""))
    tg_chat_id = st.text_input("Chat ID", value=secrets.get("tg_chat_id", ""))

if st.sidebar.button("Sauvegarder Config", type="primary"):
    save_secrets({
        "vodio_login": vodio_login,
        "vodio_password": vodio_pass,
        "tg_token": tg_token,
        "tg_chat_id": tg_chat_id
    })
    st.rerun()

st.sidebar.divider()
st.sidebar.info(f"📂 Stockage : `{BASE_DIR}`")

# Si pas de login, on bloque l'accès
if not secrets.get("vodio_login"):
    st.title("🎙️ Studio Oppodcast")
    st.error("🔒 Veuillez configurer vos identifiants Vodio dans le menu latéral.")
    st.stop()

# =========================================================
# APPLICATION PRINCIPALE
# =========================================================

# En-tête avec colonnes pour aligner
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🎙️Oppodcast Studio")
    st.caption(f"Connecté en tant que **{secrets['vodio_login']}**")

st.markdown("---")

# --- SECTION 1 : UPLOAD (DANS UN CONTENEUR CADRÉ) ---
with st.container(border=True):
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        st.subheader("Nouvel Épisode")
        st.markdown("Déposez votre fichier audio ici pour démarrer le traitement.")
    
    with col_u2:
        uploaded_file = st.file_uploader("Fichier Audio (MP3/WAV)", type=["mp3", "wav"], label_visibility="collapsed")
        
        if uploaded_file:
            with st.expander("Détails de l'épisode", expanded=True):
                title = st.text_input("Titre de l'épisode", placeholder="Ex: Mon super épisode #42")
                description = st.text_area("Description", placeholder="Description pour YouTube/Vodio...")
                
                if st.button("🚀 Mettre en file d'attente", type="primary"):
                    if title:
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
                        
                        with open(os.path.join(INBOX_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
                            json.dump(job_data, f, ensure_ascii=False, indent=4)
                        
                        st.success(f"Épisode **{title}** ajouté à la file !")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Le titre est obligatoire.")

# --- SECTION 2 : INSTAGRAM STUDIO ---
st.header("Studio Instagram")

if not InstaGenerator:
    st.error("❌ Module `insta_generator` manquant.")
else:
    with st.container(border=True):
        gen_tool = InstaGenerator()
        available_fonts = gen_tool.get_available_fonts()
        
        # Layout en 2 colonnes : Config | Prévisualisation
        col_conf, col_preview = st.columns([1, 1], gap="large")
        
        with col_conf:
            st.subheader("Personnalisation")
            
            # Onglets pour organiser les options
            tab_visuel, tab_texte = st.tabs(["Visuel", "Texte"])
            
            with tab_visuel:
                uploaded_template = st.file_uploader("Importer une Image de Fond (Optionnel)", type=["png", "jpg", "jpeg"])
                template_file = None
                if uploaded_template:
                    template_path = os.path.join(ASSETS_DIR, "temp_template.png")
                    with open(template_path, "wb") as f:
                        f.write(uploaded_template.getbuffer())
                    template_file = template_path
                    st.success("Fond chargé !")
                
                bg_color = st.color_picker("Sinon : Couleur unie", "#1E1E1E")
                
            with tab_texte:
                default_title = title if 'title' in locals() and title else "Mon Super Titre"
                insta_title = st.text_area("Titre sur l'image", value=default_title, height=100)
                insta_ep_num = st.text_input("Numéro", value="#01")
                
                c_txt1, c_txt2 = st.columns(2)
                text_color = c_txt1.color_picker("Texte", "#FFFFFF")
                accent_color = c_txt2.color_picker("Accent", "#FF4B4B")
                
                c_font1, c_font2 = st.columns(2)
                selected_font = c_font1.selectbox("Police", available_fonts)
                font_size = c_font2.slider("Taille", 30, 150, 70)

            if st.button("Générer l'Image", type="primary", use_container_width=True):
                try:
                    output_filename = f"insta_{uuid.uuid4()}.png"
                    output_path = os.path.join(GENERATED_DIR, output_filename)
                    
                    gen_tool.generate_post(
                        title=insta_title,
                        ep_number=insta_ep_num,
                        output_path=output_path,
                        bg_color=bg_color,
                        text_color=text_color,
                        accent_color=accent_color,
                        font_name=selected_font,
                        font_size=font_size,
                        background_image_path=template_file,
                        darken_bg=True
                    )
                    st.session_state["generated_img_path"] = output_path
                except Exception as e:
                    st.error(f"Erreur : {e}")

        with col_preview:
            st.subheader("Aperçu")
            if st.session_state["generated_img_path"] and os.path.exists(st.session_state["generated_img_path"]):
                img_path = st.session_state["generated_img_path"]
                st.image(img_path, caption="Post Instagram généré", use_container_width=True)
                
                c_dl, c_tg = st.columns(2)
                with c_dl:
                    with open(img_path, "rb") as file:
                        st.download_button("💾 Télécharger", data=file, file_name="post.png", mime="image/png", use_container_width=True)
                with c_tg:
                    if st.button("Envoyer Telegram", use_container_width=True):
                        if TelegramNotifier and secrets.get("tg_token"):
                            notif = TelegramNotifier(secrets["tg_token"], secrets["tg_chat_id"])
                            cap = f"🎙 {insta_title}\n\n#{insta_ep_num}"
                            if notif.send_photo(img_path, cap):
                                st.success("Envoyé !")
                            else:
                                st.error("Erreur Telegram")
                        else:
                            st.warning("Telegram non configuré")
            else:
                st.info("Cliquez sur 'Générer' pour voir le résultat.")

# --- SECTION 3 : YOUTUBE STUDIO ---
st.header("Studio YouTube")

if not YouTubeGenerator:
    st.error("❌ Module `youtube_generator` manquant (moviepy?).")
else:
    with st.container(border=True):
        col_y1, col_y2 = st.columns([1, 1], gap="large")
        
        with col_y1:
            st.subheader("1. Encodage Vidéo")
            
            # Selecteur intelligent
            mp3_files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".mp3")]
            mp3_files.sort(key=lambda x: os.path.getctime(os.path.join(INBOX_DIR, x)), reverse=True)
            
            selected_mp3 = st.selectbox("Choisir l'épisode source", options=mp3_files, format_func=get_episode_label)
            video_format = st.radio("Format Vidéo", ["Carré (1:1)", "Paysage (16:9)"], horizontal=True)
            
            current_img = st.session_state.get("generated_img_path")
            if not current_img:
                st.warning("⚠️ Générez d'abord une image Instagram ci-dessus.")
            
            if st.button("Lancer le rendu Vidéo", type="primary", disabled=(not selected_mp3 or not current_img), use_container_width=True):
                display_name = get_episode_label(selected_mp3).replace("🎙️ ", "")
                safe_name = "".join([c for c in display_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_")
                output_filename = f"{safe_name}.mp4"
                audio_path = os.path.join(INBOX_DIR, selected_mp3)
                fmt = "square" if "Carré" in video_format else "landscape"
                
                with st.spinner(f"Encodage de '{display_name}' en cours..."):
                    try:
                        yt_gen = YouTubeGenerator(output_dir=GENERATED_DIR)
                        vid_path = yt_gen.generate_video(audio_path, current_img, output_filename, format=fmt)
                        st.session_state["generated_video_path"] = vid_path
                        st.session_state["video_mp3_source"] = selected_mp3
                        st.success("Rendu terminé !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur rendu : {e}")

        with col_y2:
            st.subheader("2. Publication")
            vid_path = st.session_state.get("generated_video_path")
            
            if vid_path and os.path.exists(vid_path):
                st.video(vid_path)
                with open(vid_path, "rb") as f:
                    st.download_button("Télécharger MP4", data=f, file_name=os.path.basename(vid_path), mime="video/mp4", use_container_width=True)
                
                st.divider()
                st.markdown("**Upload YouTube**")
                
                if YouTubeUploader and os.path.exists("token.pickle"):
                    privacy = st.selectbox("Visibilité", ["private", "unlisted", "public"])
                    if st.button("Envoyer sur YouTube", type="primary", use_container_width=True):
                        # Logique upload...
                        # (Reprise de ton code existant simplifiée pour l'exemple)
                        pass
                else:
                    st.info("Configurez YouTube (token.pickle) pour uploader directement.")
            else:
                st.info("Aucune vidéo générée pour le moment.")
