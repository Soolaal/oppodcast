# Oppodcast Studio V2

**Oppodcast Studio** is a self-hosted automation dashboard designed to streamline the complete podcast publishing workflow. Originally built to automate **Vodio** uploads, it has evolved into a full production suite for social media assets and YouTube distribution.

## Features

### 1. Podcast Hosting Automation (Vodio)
*   **Queue System:** Uploads are queued locally and processed asynchronously.
*   **Headless Worker:** Uses **Playwright** to log in to the Vodio interface and upload the episode file + metadata without user intervention.
*   **Decoupled Architecture:** The web UI remains responsive while the heavy upload happens in the background.

### 2. Instagram Studio
*   **Asset Generation:** Create professional visuals (Square 1:1) instantly.
*   **Custom Templates:** Upload your own background images (supports auto-cropping/fitting).
*   **Typography Engine:** Custom font support (`.ttf`) with auto-sizing and positioning.
*   **Real-time Preview:** Adjust colors, text size, and fonts live.

### 3. YouTube Studio
*   **Video Rendering:** Converts your MP3 + Generated Image into an MP4 video.
*   **Smart Layouts:**
    *   **Square (1:1):** Optimized for LinkedIn/Instagram/Facebook feeds.
    *   **Landscape (16:9):** Classic YouTube format with an elegant blurred/darkened background effect.
*   **Direct Upload:** Publishes the generated video directly to your YouTube channel via the official API.

### 4. Notifications & delivery
*   **Telegram Integration:** Sends the final visual + caption to your phone for easy sharing.
*   **Status Updates:** Receive alerts when jobs are completed.

---

## Architecture

The application is split into components to ensure stability:

*   **Frontend (`Oppodcast.py`):** Streamlit-based web interface for user interaction.
*   **Worker (`worker.py`):** Background process watching the `inbox/` folder for Vodio uploads.
*   **Generators:** Python scripts (`youtube_generator.py`, `insta_generator.py`) handling media processing (Pillow, MoviePy).
*   **Uploader (`youtube_uploader.py`):** Handles Google OAuth2 authentication.

---

## Installation & Setup

### Prerequisites
*   **Docker** (Recommended) or Python 3.9+
*   **Google Cloud Account** (Free tier is sufficient)
*   **Telegram Account**

### 1. Directory Structure
Create a project folder with the following structure:

```text
/oppodcast/
├── Dockerfile
├── requirements.txt
├── Oppodcast.py
├── worker.py
├── youtube_uploader.py
├── youtube_generator.py
├── insta_generator.py
├── client_secret.json    <-- (See Step 3)
├── token.pickle          <-- (See Step 3)
└── assets/               <-- Place your .ttf fonts here
```
### 2. Getting Telegram Credentials

1.  Open Telegram and search for **@BotFather**.
2.  Send the command `/newbot`.
3.  Follow instructions to name your bot. You will get a **TOKEN** (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).
4.  Search for **@userinfobot** (or any ID bot) and start it to get your personal **Chat ID** (e.g., `987654321`).
5.  *Save these for the Oppodcast configuration sidebar.*

### 3. Getting YouTube/Google Credentials

**This is the most critical step.** Since Docker has no browser, you must authenticate once on your local PC.

#### Phase A: Google Cloud Console
1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project (e.g., `Oppodcast`).
3.  **Enable API:** Search for and enable **"YouTube Data API v3"**.
4.  **OAuth Consent Screen:**
    *   User Type: **External**.
    *   **Test Users:** Add your own Gmail address (Crucial!).
5.  **Credentials:**
    *   Create Credentials > **OAuth Client ID**.
    *   Type: **Desktop App**.
    *   Download the JSON file, rename it to `client_secret.json`.
    *   **Place this file in your project folder.**

#### Phase B: Generate the Token (Local PC)
1.  Install dependencies locally:
    ```bash
    pip install google-auth-oauthlib google-api-python-client
    ```
2.  Run the uploader script manually:
    ```bash
    python youtube_uploader.py
    ```
3.  A browser window will open. Log in with the Gmail account you added as a Test User.
    *   *Note: If you see "Google hasn't verified this app", click Advanced > Go to App (unsafe).*
4.  Once successful, a file named **`token.pickle`** will appear in the folder.
5.  **Copy this `token.pickle` file to your Docker/Server folder.**

---

## Docker Deployment (Home Assistant / Portainer)

### Dockerfile
Ensure your `Dockerfile` installs system dependencies for video processing:

```dockerfile
FROM python:3.9-slim

# Install system dependencies (FFmpeg is required for video)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

CMD ["streamlit", "run", "Oppodcast.py"]

```
## User Guide

### Configuration
1.  Open the Web UI (`http://your-ip:8501`).
2.  Enter your Vodio Login/Pass and Telegram Token/ID in the sidebar.
3.  Click **"Save"**.

### Workflow
*   **Step 1:** Upload your MP3 in "Nouvel Épisode".
*   **Step 2:** Go to **"Studio Instagram"**. Upload a background image (Template), customize the text, and generate the visual.
*   **Step 3:** Go to **"Studio YouTube"**. Select the format (Square or Landscape) and generate the video.
*   **Step 4:** Click **"Envoyer sur YouTube "** to publish immediately.

---

## Known Limitations

*   **Google Quotas:** Free API allows ~6 video uploads per day (10,000 units quota).
*   **Vodio Changes:** The automation relies on the Vodio website DOM. If they change their interface, the `worker.py` script might need updates.
*   **Token Expiry:** If the `token.pickle` expires (rarely happens in Testing mode), simply re-run the local generation step.


