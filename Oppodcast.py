import streamlit as st
import json
import os
import uuid

# --- CONFIGURATION ---
INBOX_DIR = "inbox"
# Persistence path for Home Assistant Add-ons
SECRETS_PATH = "/data/secrets.json"
# Fallback for local testing
if not os.path.exists("/data"):
    SECRETS_PATH = "secrets.json"

os.makedirs(INBOX_DIR, exist_ok=True)

# --- UTILS ---
def load_secrets():
    """Load credentials from persistent JSON."""
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"vodio_login": "", "vodio_password": ""}

def save_secrets(login, password):
    """Save credentials to persistent storage."""
    with open(SECRETS_PATH, "w") as f:
        json.dump({"vodio_login": login, "vodio_password": password}, f)
    st.toast("✅ Vodio credentials saved!", icon="💾")

# --- SIDEBAR (Config) ---
st.sidebar.title("🔐 Configuration")
secrets = load_secrets()

with st.sidebar.expander("Vodio Account", expanded=not secrets.get("vodio_login")):
    login_input = st.text_input("Login / ID", value=secrets.get("vodio_login", ""))
    pass_input = st.text_input("Password", value=secrets.get("vodio_password", ""), type="password")
    
    if st.button("Save Credentials"):
        save_secrets(login_input, pass_input)
        st.rerun() 

# --- BLOCKING CHECK ---
if not secrets.get("vodio_login") or not secrets.get("vodio_password"):
    st.title("🎙️ Studio Oppodcast")
    st.warning("👋 Welcome! Please configure your Vodio credentials in the sidebar to continue.")
    st.stop() 

# =========================================================
# MAIN APP
# =========================================================

st.title("🎙️ Studio Oppodcast")
st.caption(f"Connected as: {secrets['vodio_login']}")

# 1. Input Form
with st.form("new_episode"):
    st.header("New Episode")
    uploaded_file = st.file_uploader("Audio File (MP3/WAV)", type=["mp3", "wav"])
    title = st.text_input("Episode Title")
    description = st.text_area("Description")
    
    submit_btn = st.form_submit_button("Add to Queue 🚀")

# 2. Submission Handler
if submit_btn:
    if uploaded_file is not None and title:
        job_id = str(uuid.uuid4())
        
        # Save MP3
        mp3_filename = f"{job_id}.mp3"
        mp3_path = os.path.join(INBOX_DIR, mp3_filename)
        
        with open(mp3_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Save Metadata
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
            
        st.success(f"✅ Episode '{title}' added to queue! (ID: {job_id})")
        st.balloons()
        st.info("Worker is processing in the background.")
        
    else:
        st.error("⚠️ File and Title are required!")
