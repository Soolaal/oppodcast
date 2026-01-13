# Use official Playwright image (includes Python + Browsers)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Python settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

# --- CRUCIAL: Install FFmpeg for Video Generation (MoviePy) ---
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create working directories (Updated for V2)
# /data is used for secrets.json persistence
RUN mkdir -p inbox generated assets /data

# Install Chromium only (for Vodio worker)
RUN playwright install chromium

# Expose Streamlit port
EXPOSE 8501


# 2. On lance tout en une seule ligne (plus besoin de run.sh !)
CMD ["/bin/bash", "-c", "python worker.py & streamlit run Oppodcast.py --server.port=8501 --server.address=0.0.0.0"]

