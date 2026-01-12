# Studio Oppodcast

A self-hosted automation tool designed to streamline the podcast publishing workflow for Vodio.

This project allows me to upload MP3 files and metadata via a simple web interface, delegating the actual browser interaction to a background worker. It is packaged as a Home Assistant Add-on but runs on standard Docker containers.

## Architecture

The application is split into two components to ensure stability:

1.  **Frontend (Streamlit):** A web interface to input the episode title, description, and audio file. It queues jobs as JSON files in a local directory.
2.  **Worker (Python + Playwright):** A background process that watches the queue. It launches a headless Chromium instance to log in to Vodio and upload the content automatically.

This decoupled approach means the web interface remains responsive even during long uploads.

## Features

*   **Queue System:** Jobs are queued locally, allowing for asynchronous processing.
*   **Persistent Configuration:** Credentials are stored securely in the add-on data volume.
*   **Headless Automation:** Uses Playwright to navigate the Vodio dashboard without user intervention.
*   **Docker Compatible:** Runs easily as a Home Assistant Local Add-on or a standalone container.

## Installation

### As a Home Assistant Add-on

1.  Copy the `oppodcast` folder to your Home Assistant `/addons/` directory.
2.  Navigate to **Settings > Add-ons > Add-on Store**.
3.  Click the menu (three dots) and select **Check for updates**.
4.  Install **Studio Oppodcast** from the Local Add-ons section.
5.  Start the add-on and open the Web UI to configure your credentials.

### Local Development

To run the project locally without Docker for testing:

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

2.  Run the interface:
    ```bash
    streamlit run Oppodcast.py
    ```

3.  Run the worker (in a separate terminal):
    ```bash
    python worker.py
    ```

## Roadmap

*   Automatic Instagram post generation (Cover + Description).
*   YouTube video creation (Static image + Audio visualization).
*   Notification system (Telegram/Discord) upon completion.

## Disclaimer

This tool relies on web scraping/automation of a third-party platform. Changes to the Vodio interface may break the automation script until updated. Use at your own risk.
