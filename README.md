# Oppodcast Studio (Web Edition)

**Oppodcast Studio** is a self-hosted automation dashboard designed to streamline the complete podcast publishing workflow.

Originally built to automate **Vodio** uploads via a headless browser, it has evolved into a full production suite for social media assets, YouTube distribution, and a soundboard for live recording.

> **Note:** This is the **Server/Web edition**. A Desktop version (optimized for low-latency live recording) is currently in development.

---

## Features

### 1. Hosting Automation (Vodio)
*   **Queue System:** Episodes are stored locally in an `inbox/` folder and processed sequentially.
*   **Headless Worker:** A background process (using **Playwright**) logs into the Vodio interface to upload the episode file and metadata without user intervention.
*   **Decoupled Architecture:** The web UI remains responsive while heavy upload tasks occur in the background.

### 2. Instagram Studio
*   **Asset Generation:** Create professional square (1:1) visuals instantly.
*   **Custom Templates:** Upload your own background images (supports auto-darkening).
*   **Typography Engine:** Custom font support (`.ttf`) with smart positioning.
*   **Real-time Preview:** Adjust colors, text size, and fonts live.

### 3. YouTube Studio
*   **Video Rendering:** Converts your MP3 + Generated Image into an MP4 video (1080p).
*   **Smart Layouts:**
    *   **Square (1:1):** Optimized for LinkedIn/Instagram/Facebook feeds.
    *   **Landscape (16:9):** Classic YouTube format with a blurred background effect.
*   **Shorts Generator:** Automatically create 60s vertical clips (9:16) for TikTok/Reels/Shorts.
*   **Direct Upload:** Publishes the video directly to your channel via the official Google Data API.

### 4. Jingle Palette (Web)
*   **Integrated Soundboard:** Trigger intros, outros, and sound effects directly from the browser.
*   **Presets:** Create and save different sound grids for different shows.
*   **Easy Upload:** Add your MP3/WAV files via simple drag-and-drop.

---

## Technical Architecture

The application is split into components to ensure stability:

*   **Frontend (`Oppodcast.py`):** Streamlit-based web interface for user interaction.
*   **Worker (`worker.py`):** Background process monitoring the `jobs.json` file to trigger Vodio uploads.
*   **Generators:** Python scripts (`youtube_generator.py`, `insta_generator.py`) handling media processing (Pillow, MoviePy).
*   **Uploader (`youtube_uploader.py`):** Handles Google OAuth2 authentication.

---

## Installation & Configuration

### Prerequisites
*   **Docker** (Recommended) or Python 3.9+
*   **Google Cloud Account** (Free tier) for the YouTube API

### 1. Project Structure
Ensure your folder structure looks like this:

```text
/oppodcast/
├── Dockerfile
├── docker-compose.yml    <-- (Recommended)
├── requirements.txt
├── Oppodcast.py
├── worker.py
├── youtube_uploader.py
├── youtube_generator.py
├── insta_generator.py
├── jingle_palette.py
├── client_secret.json    <-- (Google Auth - See Step 2)
├── token.pickle          <-- (Google Token - See Step 2)
└── assets/               <-- Place your .ttf fonts here
```


### 2. Google/YouTube Credentials (Critical)

Since Docker has no browser, you must authenticate once on your local PC to generate the token.

**Phase A: Google Cloud Console**

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **"YouTube Data API v3"**.
3. Configure **OAuth Consent Screen** (User Type: External, add your email as "Test User").
4. Create **Credentials** -> **OAuth Client ID** (Desktop App).
5. Download the JSON, rename it to `client_secret.json`, and place it in the project root.

**Phase B: Generate Token (Local PC)**

1. Install libraries: `pip install google-auth-oauthlib google-api-python-client`
2. Run the script: `python youtube_uploader.py`
3. Log in via the browser window that opens.
4. **Copy the generated `token.pickle` file to your server/docker folder.**

---

## Docker Deployment (Portainer / Home Assistant)

Use this `docker-compose.yml` to persist your configuration and tokens.

```yaml
version: '3.8'

services:
  oppodcast:
    build: .
    container_name: oppodcast_studio
    ports:
      - "8501:8501"
    volumes:
      - ./assets:/app/assets
      - ./inbox:/app/inbox
      - ./generated:/app/generated
      - ./presets:/app/presets          # To save Jingle Palette configs
      - ./client_secret.json:/app/client_secret.json
      - ./token.pickle:/app/token.pickle
      - ./secrets.json:/app/secrets.json # To save Vodio login/pass
    restart: unless-stopped
```


---

## User Guide

### 1. Initial Configuration

Open the Web UI (`http://your-ip:8501`). Enter your Vodio credentials in the sidebar and click **Save**.

### 2. Typical Workflow

1. **New Episode:** Upload your MP3 in the "New Episode" tab. It is added to the queue, and the Worker will handle the upload to Vodio.
2. **Instagram:** Go to **"Instagram Studio"**. Choose a template, edit the text, and generate the image.
3. **YouTube:** Go to **"YouTube Studio"**. Select the format (Square/Landscape) -> Generate -> **"Upload to YouTube"**.
4. **Live:** Use the **Jingle Palette** to play your sounds during recording.

---

## Known Limitations

* **Google Quotas:** The free API allows approximately 6 video uploads per day.
* **Token Expiry:** If `token.pickle` expires, re-run Step 2 (Phase B) locally.
* **Vodio Updates:** The automation relies on the Vodio website DOM. If their interface changes, `worker.py` may need updating.
