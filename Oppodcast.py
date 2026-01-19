import streamlit as st
import json
import os
import uuid
import time
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Oppodcast Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    h1 {color: #FF4B4B; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;} 
    h2, h3 {font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;}
    .stButton button {width: 100%; border-radius: 8px; font-weight: 600;}
    div[data-testid="stExpander"] {border: 1px solid #333; border-radius: 8px;}
    div[data-baseweb="input"] {border-radius: 6px;}
    div[data-testid="stExpander"] summary p {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- IMPORTS ---
try: from insta_generator import InstaGenerator
except ImportError: InstaGenerator = None
try: from telegram_notifier import TelegramNotifier
except ImportError: TelegramNotifier = None
try: from youtube_generator import YouTubeGenerator
except ImportError: YouTubeGenerator = None
try: from youtube_uploader import YouTubeUploader
except ImportError: YouTubeUploader = None
try: from shorts_generator import ShortsGenerator 
except ImportError: ShortsGenerator = None
try: from translations import TRANS
except ImportError: 
    # Fallback si translations.py n'existe pas encore
    TRANS = {"fr": {}}
    st.error("⚠️ Fichier translations.py manquant !")

# --- GESTION DES CHEMINS ---
if os.path.exists("/share"):
    BASE_DIR = "/share/oppodcast"
else:
    BASE_DIR = os.getcwd()

INBOX_DIR = os.path.join(BASE_DIR, "inbox")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SECRETS_PATH = os.path.join(BASE_DIR, "secrets.json")

for d in [INBOX_DIR, GENERATED_DIR, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)

# --- FONCTIONS UTILITAIRES ---
def t(key):
    """Récupère le texte dans la langue choisie"""
    lang = st.session_state.get("language", "fr")
    # Retourne le texte ou la clé si introuvable, fallback sur français
    return TRANS.get(lang, TRANS.get("fr", {})).get(key, key)

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
            real_title = data.get("title", t("untitled"))
            return f"🎙️ {real_title}"
        except:
            pass
    return f"📁 {filename}"

# --- SESSION STATE ---
for key in ["generated_video_path", "generated_img_path", "video_mp3_source", "generated_short_path", "language"]:
    if key not in st.session_state:
        st.session_state[key] = None
if st.session_state["language"] is None:
    st.session_state["language"] = "fr" # Défaut

# =========================================================
# BARRE LATÉRALE
# =========================================================
secrets = load_secrets()
logo_path = os.path.join(ASSETS_DIR, "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=180)

st.sidebar.header(t("settings"))

# --- SÉLECTEUR DE LANGUE ---
# On utilise radio avec une callback pour éviter le rerun explicite inutile
# --- SÉLECTEUR DE LANGUE (AVEC DRAPEAUX) ---
col_lang = st.sidebar.container()

# Dictionnaire de mapping Code -> Drapeau
LANG_FLAGS = {
    "fr": "🇫🇷 Français",
    "en": "🇬🇧 English"
}

lang_choice = col_lang.radio(
    "Language / Langue",
    options=["fr", "en"], # Les valeurs réelles stockées
    format_func=lambda x: LANG_FLAGS.get(x, x), # Ce qui est affiché à l'écran
    index=0 if st.session_state["language"] == "fr" else 1,
    horizontal=True
)

if lang_choice != st.session_state["language"]:
    st.session_state["language"] = lang_choice
    st.rerun()


with st.sidebar.expander(t("vodio_account"), expanded=not secrets.get("vodio_login")):
    vodio_login = st.text_input(t("login"), value=secrets.get("vodio_login", ""))
    vodio_pass = st.text_input(t("password"), value=secrets.get("vodio_password", ""), type="password")

with st.sidebar.expander(t("tg_bot"), expanded=False):
    tg_token = st.text_input("Bot Token", value=secrets.get("tg_token", ""))
    tg_chat_id = st.text_input("Chat ID", value=secrets.get("tg_chat_id", ""))

if st.sidebar.button(t("save_config"), type="primary"):
    save_secrets({
        "vodio_login": vodio_login,
        "vodio_password": vodio_pass,
        "tg_token": tg_token,
        "tg_chat_id": tg_chat_id
    })
    st.rerun()

st.sidebar.divider()
st.sidebar.caption(f"{t('storage_path')} `{BASE_DIR}`")

if not secrets.get("vodio_login"):
    st.title("🎙️ Studio Oppodcast")
    st.error(t("config_error"))
    st.stop()

# =========================================================
# APPLICATION PRINCIPALE
# =========================================================

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("Oppodcast Studio")
    st.caption(f"{t('connected_as')} **{secrets['vodio_login']}**")

st.markdown("---")

# --- SECTION 1 : UPLOAD ---
with st.expander(t("s1_title"), expanded=True):
    with st.container(border=True):
        col_u1, col_u2 = st.columns([1, 2])
        with col_u1:
            st.subheader(t("s1_col_title"))
            st.markdown(t("s1_desc"))
        
        with col_u2:
            uploaded_file = st.file_uploader(t("s1_label"), type=["mp3", "wav"], label_visibility="collapsed")
            
            if uploaded_file:
                st.audio(uploaded_file, format='audio/mp3')

                with st.expander(t("ep_details"), expanded=True):
                    title = st.text_input(t("ep_title"), placeholder=t("ep_title_ph"))
                    description = st.text_area(t("ep_desc"), placeholder=t("ep_desc_ph"))
                    
                    if st.button(t("btn_queue"), type="primary"):
                        if title:
                            job_id = str(uuid.uuid4())
                            mp3_filename = f"{job_id}.mp3"
                            mp3_path = os.path.join(INBOX_DIR, mp3_filename)
                            with open(mp3_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            job_data = {
                                "id": job_id, "title": title, "description": description,
                                "mp3_file": mp3_filename, "status": "pending",
                                "created_at": str(os.path.getctime(mp3_path))
                            }
                            with open(os.path.join(INBOX_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
                                json.dump(job_data, f, ensure_ascii=False, indent=4)
                            st.success(f"{t('success_queue')} ({title})")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(t("err_title"))

# --- SECTION 2 : INSTAGRAM STUDIO ---
with st.expander(t("s2_title"), expanded=False):
    if not InstaGenerator:
        st.error(t("mod_missing"))
    else:
        with st.container(border=True):
            gen_tool = InstaGenerator()
            available_fonts = gen_tool.get_available_fonts()
            col_conf, col_preview = st.columns([1, 1], gap="large")
            
            with col_conf:
                st.subheader(t("custom"))
                tab_visuel, tab_texte = st.tabs([t("tab_visual"), t("tab_text")])
                with tab_visuel:
                    uploaded_template = st.file_uploader(t("upload_bg"), type=["png", "jpg", "jpeg"])
                    template_file = None
                    if uploaded_template:
                        template_path = os.path.join(ASSETS_DIR, "temp_template.png")
                        with open(template_path, "wb") as f: f.write(uploaded_template.getbuffer())
                        template_file = template_path
                        st.success(t("bg_loaded"))
                    bg_color = st.color_picker(t("color_bg"), "#1E1E1E")
                    
                with tab_texte:
                    default_title = title if 'title' in locals() and title else "Mon Super Titre"
                    insta_title = st.text_area(t("txt_on_img"), value=default_title, height=100)
                    insta_ep_num = st.text_input(t("txt_ep_num"), value="#01")
                    c_txt1, c_txt2 = st.columns(2)
                    text_color = c_txt1.color_picker(t("color_txt"), "#FFFFFF")
                    accent_color = c_txt2.color_picker(t("color_accent"), "#FF4B4B")
                    c_font1, c_font2 = st.columns(2)
                    selected_font = c_font1.selectbox(t("font"), available_fonts)
                    font_size = c_font2.slider(t("size"), 30, 150, 70)

                if st.button(t("btn_gen_img"), type="primary", use_container_width=True):
                    try:
                        output_filename = f"insta_{uuid.uuid4()}.png"
                        output_path = os.path.join(GENERATED_DIR, output_filename)
                        gen_tool.generate_post(
                            title=insta_title, ep_number=insta_ep_num, output_path=output_path,
                            bg_color=bg_color, text_color=text_color, accent_color=accent_color,
                            font_name=selected_font, font_size=font_size,
                            background_image_path=template_file, darken_bg=True
                        )
                        st.session_state["generated_img_path"] = output_path
                    except Exception as e: st.error(f"{t('err_gen_img')} : {e}")

            with col_preview:
                st.subheader(t("preview"))
                if st.session_state["generated_img_path"] and os.path.exists(st.session_state["generated_img_path"]):
                    img_path = st.session_state["generated_img_path"]
                    st.image(img_path, caption="Post Instagram généré", use_container_width=True)
                    c_dl, c_tg = st.columns(2)
                    with c_dl:
                        with open(img_path, "rb") as file:
                            st.download_button(t("btn_dl"), data=file, file_name="post.png", mime="image/png", use_container_width=True)
                    with c_tg:
                        if st.button(t("btn_tg"), use_container_width=True):
                            if TelegramNotifier and secrets.get("tg_token"):
                                notif = TelegramNotifier(secrets["tg_token"], secrets["tg_chat_id"])
                                cap = f"🎙 {insta_title}\n\n#{insta_ep_num}"
                                if notif.send_photo(img_path, cap): st.success(t("sent_tg"))
                                else: st.error(t("err_tg"))
                            else: st.warning(t("warn_tg"))
                else: st.info(t("info_click_gen"))

# --- SECTION 3 : YOUTUBE STUDIO ---
with st.expander(t("s3_title"), expanded=False):
    if not YouTubeGenerator:
        st.error(t("mod_missing"))
    else:
        with st.container(border=True):
            col_y1, col_y2 = st.columns([1, 1], gap="large")
            
            with col_y1:
                st.subheader(t("create_vid"))
                mp3_files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".mp3")]
                mp3_files.sort(key=lambda x: os.path.getctime(os.path.join(INBOX_DIR, x)), reverse=True)
                
                selected_mp3 = st.selectbox(t("choose_ep"), options=mp3_files, format_func=get_episode_label)
                video_format = st.radio(t("vid_format"), [t("fmt_square"), t("fmt_landscape")], horizontal=True)
                
                st.divider()
                st.markdown(f"##### {t('perf_settings')}")
                # CHOIX DU MODE DE RENDU
                render_mode = st.selectbox(
                    t("render_mode"),
                    options=["turbo", "balanced", "quality"],
                    format_func=lambda x: {
                        "turbo": t("turbo_desc"),
                        "balanced": t("balanced_desc"),
                        "quality": t("quality_desc")
                    }[x]
                )
                
                bg_color_hex = "#000000"
                if render_mode == "turbo":
                    bg_color_hex = st.color_picker(t("bg_color"), "#101010")

                current_img = st.session_state.get("generated_img_path")
                if not current_img:
                    st.warning(t("warn_img"))
                
                if st.button(t("btn_render_vid"), type="primary", disabled=(not selected_mp3 or not current_img), use_container_width=True):
                    display_name = get_episode_label(selected_mp3).replace("🎙️ ", "")
                    safe_name = "".join([c for c in display_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(" ", "_")
                    output_filename = f"{safe_name}.mp4"
                    audio_path = os.path.join(INBOX_DIR, selected_mp3)
                    fmt = "square" if t("fmt_square") in video_format else "landscape"
                    
                    progress_container = st.empty()
                    progress_bar = progress_container.progress(0, text=t("init_enc"))
                    def update_progress(percent): progress_bar.progress(percent, text=f"{t('encoding')} {percent}%")
                    
                    try:
                        yt_gen = YouTubeGenerator(output_dir=GENERATED_DIR)
                        vid_path = yt_gen.generate_video(
                            audio_path, current_img, output_filename, format=fmt,
                            progress_callback=update_progress,
                            render_mode=render_mode,   # <--- mode
                            bg_color=bg_color_hex      # <--- couleur
                        )
                        progress_bar.progress(100, text="100% !")
                        time.sleep(0.5)
                        progress_container.empty()
                        st.session_state["generated_video_path"] = vid_path
                        st.session_state["video_mp3_source"] = selected_mp3
                        st.success(t("success_render"))
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        progress_container.empty()
                        st.error(f"Erreur : {e}")

            with col_y2:
                st.subheader(t("preview"))
                vid_path = st.session_state.get("generated_video_path")
                if vid_path and os.path.exists(vid_path):
                    st.video(vid_path)
                    with open(vid_path, "rb") as f:
                        st.download_button("Télécharger MP4", data=f, file_name=os.path.basename(vid_path), mime="video/mp4", use_container_width=True)
                    st.divider()
                    if YouTubeUploader and os.path.exists("token.pickle"):
                        privacy = st.selectbox(t("visibility"), ["private", "unlisted", "public"])
                        if st.button(t("btn_send_yt"), type="primary", use_container_width=True):
                            try:
                                uploader = YouTubeUploader()
                                json_path = os.path.join(INBOX_DIR, st.session_state["video_mp3_source"].replace(".mp3", ".json"))
                                vid_title = get_episode_label(st.session_state["video_mp3_source"]).replace("🎙️ ", "")
                                vid_desc = "Généré par Oppodcast."
                                if os.path.exists(json_path):
                                    with open(json_path, "r") as f:
                                        d = json.load(f)
                                        vid_title = d.get("title", vid_title)
                                        vid_desc = d.get("description", vid_desc)
                                link = uploader.upload_video(vid_path, vid_title, vid_desc, privacy=privacy)
                                st.success(f"{t('online_link')}({link})")
                            except Exception as e: st.error(f"Erreur Upload : {e}")
                    else: st.info(t("configure_yt"))
                else: st.info(t("info_no_vid"))

# --- SECTION 4 : STUDIO SHORTS ---
with st.expander(t("s4_title"), expanded=False):
    if not ShortsGenerator:
        st.warning(t("mod_missing"))
    else:
        with st.container(border=True):
            col_s1, col_s2 = st.columns([1, 1], gap="large")
            with col_s1:
                st.subheader(t("create_short"))
                if 'selected_mp3' not in locals() or not selected_mp3 or not st.session_state["generated_img_path"]:
                    st.warning(t("warn_img"))
                else:
                    st.info(f"{t('info_source')} {get_episode_label(selected_mp3)}")
                    c_t1, c_t2 = st.columns(2)
                    start_time = c_t1.number_input(t("start_sec"), min_value=0, value=0)
                    duration = c_t2.number_input(t("dur_sec"), min_value=15, max_value=60, value=58) 
                    
                    st.divider()
                    st.markdown(f"##### {t('perf_settings')}")
                    # CHOIX DU MODE DE RENDU (SHORTS)
                    short_render_mode = st.selectbox(
                        t("render_mode_short"),
                        options=["turbo", "balanced", "quality"],
                        format_func=lambda x: {
                            "turbo": t("turbo_desc"),
                            "balanced": t("balanced_desc"),
                            "quality": t("quality_desc")
                        }[x],
                        key="short_mode"
                    )
                    short_bg_color = "#000000"
                    if short_render_mode == "turbo":
                        short_bg_color = st.color_picker(t("bg_color_short"), "#101010", key="short_color")

                    if st.button(t("btn_gen_short"), type="primary"):
                        short_name = f"short_{uuid.uuid4()}.mp4"
                        audio_full_path = os.path.join(INBOX_DIR, selected_mp3)
                        img_full_path = st.session_state["generated_img_path"]
                        
                        progress_short_container = st.empty()
                        progress_short = progress_short_container.progress(0, text=t("init_short"))
                        def update_short_bar(percent): progress_short.progress(percent, text=f"{t('gen_short')} {percent}%")
                        
                        try:
                            sg = ShortsGenerator(output_dir=GENERATED_DIR)
                            short_path = sg.generate_short(
                                audio_full_path, img_full_path, 
                                start_time=start_time, duration=duration, 
                                output_filename=short_name,
                                progress_callback=update_short_bar,
                                render_mode=short_render_mode, # <--- Mode
                                bg_color=short_bg_color        # <--- Couleur
                            )
                            progress_short.progress(100, text="100% !")
                            time.sleep(0.5)
                            progress_short_container.empty()
                            st.session_state["generated_short_path"] = short_path
                            st.success("Short généré !")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            progress_short_container.empty()
                            st.error(f"Erreur : {e}")

            with col_s2:
                st.subheader(t("preview"))
                short_current = st.session_state.get("generated_short_path")
                if short_current and os.path.exists(short_current):
                    st.video(short_current)
                    with open(short_current, "rb") as f:
                        st.download_button(t("btn_dl"), data=f, file_name="short_reels.mp4", mime="video/mp4", use_container_width=True)
                    st.divider()
                    if YouTubeUploader and os.path.exists("token.pickle"):
                        privacy_short = st.selectbox(t("vis_short"), ["private", "unlisted", "public"], key="privacy_short")
                        if st.button(t("btn_send_short"), type="primary", use_container_width=True):
                            try:
                                uploader = YouTubeUploader()
                                base_title = get_episode_label(selected_mp3).replace("🎙️ ", "")
                                short_title = f"{base_title} #Shorts"
                                short_desc = f"Extrait de l'épisode : {base_title}\n\nGénéré par Oppodcast #Shorts"
                                with st.spinner(t("uploading_short")):
                                    link = uploader.upload_video(short_current, short_title, short_desc, privacy=privacy_short)
                                    st.success(f"{t('short_online')}({link})")
                                    st.balloons()
                            except Exception as e: st.error(f"Erreur Upload : {e}")
                    else: st.info(t("configure_yt"))
                else: st.info(t("config_gen_first"))

# --- 5. HISTORIQUE ---
with st.expander(t("hist_title"), expanded=False):
    history_files = [f for f in os.listdir(INBOX_DIR) if f.endswith(".json")]
    history_files.sort(key=lambda x: os.path.getctime(os.path.join(INBOX_DIR, x)), reverse=True)
    if history_files:
        history_data = []
        for f in history_files[:5]:
            try:
                with open(os.path.join(INBOX_DIR, f), "r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
                    date_str = datetime.fromtimestamp(float(data.get("created_at", 0))).strftime("%d/%m %H:%M")
                    history_data.append({
                        t("date"): date_str, 
                        t("title"): data.get("title"), 
                        t("status"): data.get("status", "N/A"), 
                        t("id"): data.get("id")[:8]
                    })
            except: pass
        st.dataframe(history_data, use_container_width=True, hide_index=True)
    else: st.caption(t("hist_none"))
