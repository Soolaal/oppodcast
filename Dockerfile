# Use official Playwright image (includes Python + Browsers)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Python settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create working directories
RUN mkdir -p inbox processed failed logs

# Install Chromium only
RUN playwright install chromium

# Expose Streamlit port
EXPOSE 8501

# Start Worker and Streamlit in parallel
CMD ["/bin/bash", "-c", "python worker.py & streamlit run Oppodcast.py"]
