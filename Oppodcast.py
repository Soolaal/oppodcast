import streamlit as st
import json
import os
import uuid
import time
from datetime import datetime

# --- FONCTION CRITIQUE : FILE D'ATTENTE ---
def add_job_to_queue(job_data):
    """Ajoute une tâche au fichier centralisé jobs.json"""
    jobs_file = "jobs.json"
    if os.path.exists(jobs_file):
        try:
            with open(jobs_file, "r") as f: jobs = json.load(f)
        except: jobs = {}
    else:
        jobs = {}
    
    jobs[job_data["id"]] = job_data
    
    # Sauvegarde atomique
    temp_file = f"{jobs_file}.tmp"
    with open(temp_file, "w") as f:
        json.dump(jobs, f, indent=4)
    os.replace(temp_file, jobs_file)

# --- NOTIFICATIONS WORKER ---
def check_job_notifications():
    if not os.path.exists("jobs.json"): return
    try:
        with open("jobs.json", "r") as f: jobs = json.load(f)
        if "notified_jobs" not in st.session_state: st.session_state["notified_jobs"] = set()
        for jid, data in jobs.items():
            state_key = f"{jid}_{data['status']}"
            if state_key not in st.session_state["notified_jobs"]:
                if data["status"] == "completed":
                    st.toast(f"✅ Tâche terminée : {data.get('type', 'Job')}", icon="🎉")
                    st.session_state["notified_jobs"].add(state_key)
                elif data["status"] == "failed":
                    st.error(f"❌ Échec tâche {data.get('type')} : {data.get('error', 'Erreur inconnue')}", icon="🚨")
                    st.session_state["notified_jobs"].add(state_key)
    except Exception: pass

check_job_notifications()

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Oppodcast Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PRO (Style amélioré) ---
st.markdown("""
<style>
    /* 1. Structure Globale */
    .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* 2. Typographie "Pro" */
    h1 {
        color: #FF4B4B; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
        font-size: 2.5rem !important;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #FAFAFA;
    }
    
    /* 3. Carte / Expander */
    div[data-testid="stExpander"] {
        border: 1px solid #444 !important;
        border-radius: 12px !important;
        background-color: #1E1E1E !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
    }
    
    div[data-testid="stExpander"] summary {
        background-color: #262730 !important;
        border-radius: 12px 12px 0 0 !important;
        padding: 1rem !important;
    }

    div[data-testid="stExpander"] summary p {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #FFF !important;
    }
    
    div[data-testid="stExpander"] > div[role="group"] {
        padding: 1.5rem;
    }

    /* 4. Boutons & Inputs */
    .stButton button {
        border-radius: 8px; 
        font-weight: 600; 
        font-size: 1rem;
        height: 3rem;
        transition: all 0.2s;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
    
    div[data-baseweb="input"] {
        border-radius: 8px;
        background-color: #0E1117;
        border: 1px solid #333;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #0E1117;
        border-radius: 8px;
        border: 1px solid #333;
    }

       /* 7. Radio Buttons Style "Cards" (Sidebar Fix) */
    
    /* Cible le conteneur principal du widget radio */
    div[role="radiogroup"] {
        background-color: transparent !important;
        border: none !important;
        display: flex !important;
        flex-direction: row !important;
        width: 100% !important;
        gap: 10px !important;
    }

    /* Force chaque option à être un bloc flexible */
    div[role="radiogroup"] > label {
        flex: 1 1 0px !important; /* Force la même largeur pour tous */
        width: 100% !important;   /* Prend toute la place dispo dans son flex-item */
        margin: 0 !important;
        padding: 10px !important;
        background-color: #262730 !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
        cursor: pointer !important;
    }

    /* Cache le petit rond moche de Streamlit */
    div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    /* Style du texte à l'intérieur */
    div[role="radiogroup"] label > div:last-child {
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Style sélectionné (Streamlit ajoute data-checked="true" au div interne) */
    /* Astuce : on ne peut pas facilement cibler le parent en CSS pur, 
       donc on cible le survol et le focus pour l'effet visuel. */
    
    div[role="radiogroup"] label:hover {
        border-color: #FF4B4B !important;
        background-color: #333 !important;
    }
    
    /* Effet au survol */
    div[role="radiogroup"] label:hover {
        border-color: #FF4B4B;
        background-color: #2d2f36;
    }
    
    /* Style quand c'est sélectionné (Checked) - Streamlit met un div spécifique autour */
    div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
        /* C'est le petit rond, on peut le garder ou le cacher */
    }
    
    p, label { color: #E0E0E0 !important; }
    hr { margin: 2rem 0; border-color: #444; }
</style>
""", unsafe_allow_html=True)


# --- IMPORTS ---
try: from insta_generator import InstaGenerator
except ImportError: InstaGenerator = None
# Telegram supprimé ici
try: from youtube_generator import YouTubeGenerator
except ImportError: YouTubeGenerator = None
try: from youtube_uploader import YouTubeUploader
except ImportError: YouTubeUploader = None
try: from shorts_generator import ShortsGenerator 
except ImportError: ShortsGenerator = None
try: from translations import TRANS
except ImportError: 
    TRANS = {"fr": {}}
    st.error("⚠️ Fichier translations.py manquant !")

# --- GESTION DES CHEMINS ---
USER_DOCS = os.path.expanduser("~/Documents")
BASE_DIR = os.path.join(USER_DOCS, "Oppodcast Studio")

# On s'assure que les dossiers existent
INBOX_DIR = os.path.join(BASE_DIR, "inbox")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SECRETS_PATH = os.path.join(BASE_DIR, "secrets.json")

for d in [INBOX_DIR, GENERATED_DIR, ASSETS_DIR]: os.makedirs(d, exist_ok=True)

# --- FONCTIONS UTILITAIRES ---
def t(key):
    lang = st.session_state.get("language", "fr")
    return TRANS.get(lang, TRANS.get("fr", {})).get(key, key)

def load_secrets():
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r") as f: return json.load(f)
        except: pass
    return {}

def save_secrets(data_dict):
    current = load_secrets()
    current.update(data_dict)
    with open(SECRETS_PATH, "w") as f: json.dump(current, f)
    st.toast("Identifiants sauvegardés !", icon="💾")

def get_episode_label(filename):
    json_name = filename.replace(".mp3", ".json")
    json_path = os.path.join(INBOX_DIR, json_name)
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return f"🎙️ {data.get('title', t('untitled'))}"
        except: pass
    return f"📁 {filename}"

# --- SESSION STATE ---
for key in ["generated_video_path", "generated_img_path", "video_mp3_source", "generated_short_path", "language"]:
    if key not in st.session_state: st.session_state[key] = None
if st.session_state["language"] is None: st.session_state["language"] = "fr"

# =========================================================
# BARRE LATÉRALE
# =========================================================
secrets = load_secrets()
logo_path = os.path.join(ASSETS_DIR, "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width='stretch')
else:
    st.sidebar.title("🎙️ Oppodcast")

st.sidebar.header(t("settings"))

# --- SÉLECTEUR DE LANGUE (Boutons Toggle Propres) ---
st.sidebar.markdown("**Language / Langue**")
col_fr, col_en = st.sidebar.columns(2, gap="small")

current_lang = st.session_state.get("language", "fr")

with col_fr:
    if st.button(
        "🇫🇷 Français", 
        key="btn_fr",
        type="primary" if current_lang == "fr" else "secondary",
        width='stretch'
    ):
        if current_lang != "fr":
            st.session_state["language"] = "fr"
            st.rerun()

with col_en:
    if st.button(
        "🇬🇧 English", 
        key="btn_en",
        type="primary" if current_lang == "en" else "secondary",
        width='stretch'
    ):
        if current_lang != "en":
            st.session_state["language"] = "en"
            st.rerun()

st.sidebar.divider()

with st.sidebar.expander(t("vodio_account"), expanded=not secrets.get("vodio_login")):
    vodio_login = st.text_input(t("login"), value=secrets.get("vodio_login", ""))
    vodio_pass = st.text_input(t("password"), value=secrets.get("vodio_password", ""), type="password")

# Section Telegram supprimée de la sidebar

if st.sidebar.button(t("save_config"), type="primary"):
    save_secrets({"vodio_login": vodio_login, "vodio_password": vodio_pass})
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
                                "id": job_id,
                                "type": "upload_vodio",
                                "title": title,
                                "description": description,
                                "mp3_file": mp3_filename,
                                "audio_path": mp3_path,
                                "status": "pending",
                                "created_at": time.time(),
                                "progress": 0
                            }
                            
                            add_job_to_queue(job_data)
                            
                            with open(os.path.join(INBOX_DIR, f"{job_id}.json"), "w", encoding="utf-8") as f:
                                json.dump(job_data, f, ensure_ascii=False, indent=4)

                            st.success(f"✅ {title} ajouté à la file d'attente !")
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

                if st.button(t("btn_gen_img"), type="primary", width='stretch'):
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
                    st.image(img_path, caption="Post Instagram généré", width='stretch')
                    with open(img_path, "rb") as file:
                        st.download_button(t("btn_dl"), data=file, file_name="post.png", mime="image/png", width='stretch')
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
                
                if st.button(t("btn_render_vid"), type="primary", disabled=(not selected_mp3 or not current_img), width='stretch'):
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
                            render_mode=render_mode,
                            bg_color=bg_color_hex
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
                        st.download_button("Télécharger MP4", data=f, file_name=os.path.basename(vid_path), mime="video/mp4", width='stretch')
                    st.divider()
                    if YouTubeUploader and os.path.exists("token.pickle"):
                        privacy = st.selectbox(t("visibility"), ["private", "unlisted", "public"])
                        if st.button(t("btn_send_yt"), type="primary", width='stretch'):
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
                                render_mode=short_render_mode,
                                bg_color=short_bg_color
                            )
                            progress_short.progress(100, text="100% !")
                            time.sleep(0.5)
                            progress_short_container.empty()
                            st.session_state["generated_short_path"] = short_path
                            st.success("Short généré ! ")
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
                        st.download_button(t("btn_dl"), data=f, file_name="short_reels.mp4", mime="video/mp4", width='stretch')
                    st.divider()
                    if YouTubeUploader and os.path.exists("token.pickle"):
                        privacy_short = st.selectbox(t("vis_short"), ["private", "unlisted", "public"], key="privacy_short")
                        if st.button(t("btn_send_short"), type="primary", width='stretch'):
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
        st.dataframe(history_data, width='stretch', hide_index=True)
    else: st.caption(t("hist_none"))
