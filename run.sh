#!/bin/bash

echo "Starting Podcast Automation Container..."

# 1. Start Worker in background
echo "Starting Worker..."
python worker.py &

# 2. Start Streamlit in foreground
echo "Starting Streamlit Interface..."
streamlit run Oppodcast.py --server.port=8501 --server.address=0.0.0.0
