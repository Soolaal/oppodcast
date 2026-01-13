import streamlit as st
import json
import os
import uuid
import time

# --- OPTIONAL IMPORTS (Gestion d'erreurs robuste) ---
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

# --- CONFIGURATION ---
INBOX_DIR = "inbox"
SECRETS_PATH = "/data/secrets.json"
if not os.path.exists("/data"):
    SECRETS_PATH = "secrets.json"

os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs("generated", exist_ok=True)
os.makedirs("assets", exist_ok=True)

# --- UTILS ---
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
    st.toast("✅ Identifiants sauvegardés !", icon="💾")

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

# --- SESSION STATE INIT ---
if "generated_video_path" not in st.session_state:
    st.session_state["generated_video_path"] = None

if "generated_img_path" not in st.session_state:
    st.session_state["generated_img_path"] = None

if "video_mp3_source" not in st.session_state:
    st.session_state["video_mp3_source"] = None

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🔐 Configuration")
secrets = load_secrets()

with st.sidebar.expander("🎙️ Compte Vodio", expanded=not secrets.get("vodio_login")):
    vodio_login = st.text_input("Identifiant Vodio", value=secrets.get("vodio_login", ""))
    vodio_pass = st.text_input("Mot de passe Vodio", value=secrets.get("vodio_password", ""), type="password")

with st.sidebar.expander("🔔 Notifications Telegram", expanded=False):
    tg_token = st.text_input("Bot Token", value=secrets.get("tg_token", ""))
    tg_chat_id = st.text_input("Chat ID", value=secrets.get("tg_chat_id", ""))

if st.sidebar.button("Sauvegarder les accès"):
    save_secrets({
        "vodio_login": vodio_login,
        "vodio_password": vodio_pass,
        "tg_token": tg_token,
        "tg_chat_id": tg_chat_id
    })
    st.rerun()

if not secrets.get("vodio_login") or not secrets.get("vodio_password"):
    st.title("🎙️ Studio Oppodcast")
    st.warning("👋 Bienvenue ! Veuillez configurer vos accès à gauche.")
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

    if submit_btn and uploaded_file and title:
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
        
        st.success(f"✅ Épisode '{title}' ajouté !")

st.divider()

# --- 2. INSTAGRAM STUDIO ---
st.header("📸 Studio Instagram")

if not InstaGenerator:
    st.warning("⚠️ Module 'insta_generator' manquant ou erreur d'import.")
else:
    gen_tool = InstaGenerator()
    available_fonts = gen_tool.get_available_fonts()
    
    col_conf, col_preview = st.columns([1, 1])
    
    with col_conf:
        st.subheader("1. Design & Fond")
        
        # --- UPLOAD IMAGE DE FOND (VISIBLE DIRECTEMENT) ---
        uploaded_template = st.file_uploader("🖼️ Importer une Image de Fond (Optionnel)", type=["png", "jpg", "jpeg"])
        
        template_file = None
        if uploaded_template:
            template_path = os.path.join("assets", "temp_template.png")
            with open(template_path, "wb") as f:
                f.write(uploaded_template.getbuffer())
            template_file = template_path
            st.success("Image de fond chargée !")

        bg_color = st.color_picker("Sinon : Couleur de fond", "#1E1E1E")
        
        st.subheader("2. Texte")
        default_title = title if title else "Mon Super Titre"
        insta_title = st.text_area("Titre", value=default_title, height=80)
        insta_ep_num = st.text_input("Numéro", value="#01")
        
        c1, c2 = st.columns(2)
        text_color = c1.color_picker("Couleur Texte", "#FFFFFF")
        accent_color = c2.color_picker("Couleur Accent", "#FF4B4B")
        
        st.subheader("3. Typo")
        c3, c4 = st.columns(2)
        selected_font = c3.selectbox("Police", available_fonts)
        font_size = c4.slider("Taille", 30, 150, 70)
        
        if st.button("Générer l'aperçu ✨", type="primary"):
            try:
                output_filename = f"insta_{uuid.uuid4()}.png"
                output_path = os.path.join("generated", output_filename)
                
                # APPEL AVEC NOUVEAUX PARAMETRES
                gen_tool.generate_post(
                    title=insta_title,
                    ep_number=insta_ep_num,
                    output_path=output_path,
                    bg_color=bg_color,
                    text_color=text_color,
                    accent_color=accent_color,
                    font_name=selected_font,
                    font_size=font_size,
                    background_image_path=template_file, # <--- Passage de l'image
                    darken_bg=True # Optionnel
                )
                
                st.session_state["generated_img_path"] = output_path
                
            except Exception as e:
                st.error(f"Erreur Génération Image : {e}")

    with col_preview:
        if st.session_state["generated_img_path"] and os.path.exists(st.session_state["generated_img_path"]):
            img_path = st.session_state["generated_img_path"]
            
            # Utilisation de use_container_width pour éviter le warning
            st.image(img_path, caption="Résultat Final", use_container_width=True)
            
            c_dl, c_tg = st.columns(2)
            with c_dl:
                with open(img_path, "rb") as file:
                    st.download_button("💾 Télécharger", data=file, file_name="post.png", mime="image/png")
            
            with c_tg:
                if st.button("📲 Envoyer Telegram"):
                    if TelegramNotifier and secrets.get("tg_token"):
                        notif = TelegramNotifier(secrets["tg_token"], secrets["tg_chat_id"])
                        caption = f"🎙️ {insta_title}\n\n{description}\n\n#{insta_ep_num}"
                        if notif.send_photo(img_path, caption):
                            st.success("Envoyé !")
                        else:
                            st.error("Erreur Telegram.")
                    else:
                        st.error("Configurez Telegram.")

st.divider()

# --- 3. YOUTUBE STUDIO ---
st.header("🎬 Studio YouTube")

if not YouTubeGenerator:
    st.warning("⚠️ Module YouTube manquant (moviepy non installé ?).")
else:
    col_y1, col_y2 = st.columns([1, 2])
    
    with col_y1:
        # --- SELECTEUR D'EPISODE ---
        try:
            mp3_files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".mp3")]
            mp3_files.sort(key=lambda x: os.path.getctime(os.path.join(INBOX_DIR, x)), reverse=True)
        except:
            mp3_files = []
        
        selected_mp3 = st.selectbox("Choisir l'épisode", options=mp3_files, format_func=get_episode_label)
        video_format = st.radio("Format", ["Carré (1:1)", "Paysage (16:9)"], index=0)
        
        current_img = st.session_state.get("generated_img_path")
        if current_img:
            st.success("✅ Image prête")
            st.image(current_img, width=150)
        else:
            st.info("⚠️ Veuillez générer une image Instagram d'abord.")

        if st.button("Lancer le rendu Vidéo 🎞️"):
            if not selected_mp3 or not current_img:
                st.error("Audio ou Image manquant.")
            else:
                display_name = get_episode_label(selected_mp3).replace("🎙️ ", "")
                safe_name = "".join([c for c in display_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_")
                output_filename = f"{safe_name}.mp4"
                audio_full_path = os.path.join(INBOX_DIR, selected_mp3)
                
                fmt_code = "square" if "Carré" in video_format else "landscape"
                
                with st.spinner(f"🎬 Encodage de '{display_name}'..."):
                    try:
                        yt_gen = YouTubeGenerator(output_dir="generated")
                        video_path = yt_gen.generate_video(audio_full_path, current_img, output_filename, format=fmt_code)
                        
                        st.session_state["generated_video_path"] = video_path
                        st.session_state["video_mp3_source"] = selected_mp3
                        st.success("✅ Rendu terminé !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur Génération Vidéo : {e}")

    with col_y2:
        # --- AFFICHAGE ET UPLOAD (PERSISTANT) ---
        video_path = st.session_state.get("generated_video_path")
        if video_path and os.path.exists(video_path):
            st.subheader("📺 Aperçu & Publication")
            st.video(video_path)
            
            with open(video_path, "rb") as f:
                st.download_button("Télécharger le MP4 📥", data=f, file_name=os.path.basename(video_path), mime="video/mp4")
            
            st.divider()
            
            # --- UPLOAD FORM ---
            st.caption("Envoyer sur YouTube")
            if not YouTubeUploader:
                st.warning("Module Uploader manquant.")
            elif not os.path.exists("token.pickle"):
                st.error("⚠️ Fichier 'token.pickle' manquant.")
            else:
                c_priv, c_btn = st.columns([1, 1])
                privacy = c_priv.selectbox("Visibilité", ["private", "unlisted", "public"], index=0)
                
                if c_btn.button("Envoyer sur YouTube 🔴"):
                    source_mp3 = st.session_state.get("video_mp3_source")
                    if not source_mp3: source_mp3 = selected_mp3
                    
                    display_name = get_episode_label(source_mp3).replace("🎙️ ", "")
                    json_path = os.path.join(INBOX_DIR, source_mp3.replace(".mp3", ".json"))
                    
                    vid_title = display_name
                    vid_desc = description if description else "Généré par Oppodcast."
                    
                    if os.path.exists(json_path):
                        with open(json_path, "r") as f:
                            d = json.load(f)
                            vid_title = d.get("title", vid_title)
                            vid_desc = d.get("description", vid_desc)
                    
                    with st.spinner("Authentification & Upload..."):
                        try:
                            uploader = YouTubeUploader()
                            link = uploader.upload_video(video_path, vid_title, vid_desc, privacy=privacy)
                            st.success(f"✅ En ligne ! [Voir la vidéo]({link})")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Erreur Upload : {e}")
