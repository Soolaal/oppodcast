import subprocess
import time
import webbrowser
import os
import signal
import sys

def run_app():
    print("Démarrage d'Oppodcast Studio...")


    worker_process = subprocess.Popen([sys.executable, "worker.py"])
    print(f"Worker démarré (PID: {worker_process.pid})")

    streamlit_cmd = [sys.executable, "-m", "streamlit", "run", "Oppodcast_Studio.py", "--server.headless=true"]
    streamlit_process = subprocess.Popen(streamlit_cmd)
    print(f"Streamlit démarré (PID: {streamlit_process.pid})")


    time.sleep(3)
    webbrowser.open("http://localhost:8501")

    print("\nAppuyez sur Ctrl+C pour tout arrêter.")

    try:
        worker_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\nArrêt en cours...")
        worker_process.terminate()
        streamlit_process.terminate()
        print("Tout est éteint. À bientôt !")

if __name__ == "__main__":
    run_app()
