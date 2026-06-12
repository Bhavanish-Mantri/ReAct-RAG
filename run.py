import os
import sys
import time
import webbrowser
import platform

# Prevent Windows WMI/COM hang in python's platform module
platform.win32_ver = lambda *a, **k: ('10', '10.0.22631', '', 'Multiprocessor Free')
platform.system = lambda *a, **k: 'Windows'
def _mock_uname(*a, **k):
    from collections import namedtuple
    UnameResult = namedtuple('uname_result', 'system node release version machine processor')
    return UnameResult(system='Windows', node='DESKTOP', release='10', version='10.0.22631', machine='AMD64', processor='Intel')
platform.uname = _mock_uname

from threading import Thread
import uvicorn
from dotenv import load_dotenv

# Try to load environment variables from .env
load_dotenv()

def create_env_if_missing():
    """Create template .env and .env.example files if they do not exist."""
    env_content = (
        "# Google Gemini API Key (Required for ReAct Agent LLM)\n"
        "GEMINI_API_KEY=\n\n"
        "# TMDB API Key (Optional - If left blank, the agent automatically falls back to a mock local database)\n"
        "TMDB_API_KEY=\n\n"
        "# Server Settings\n"
        "HOST=127.0.0.1\n"
        "PORT=8000\n"
    )
    
    # Write .env.example always
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_content)
        
    # Write .env only if missing
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("[INFO] Created template '.env' file. Please edit it and add your GEMINI_API_KEY.")

def open_browser():
    """Wait for server startup and open the application in the web browser."""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[INFO] Opening application in default web browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    create_env_if_missing()
    
    # Check if Gemini key is present in env
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        print("[WARNING] GEMINI_API_KEY is not set in your .env file or environment!")
        print("[WARNING] The agent will fail to initialize without a valid LLM key.")
        print("[WARNING] Please add GEMINI_API_KEY=your_key_here to the '.env' file.\n")
    
    # Start browser thread
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start Uvicorn FastAPI Server
    print("[INFO] Starting FastAPI server...")
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )
