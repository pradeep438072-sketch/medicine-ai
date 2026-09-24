import os
import sys
from pathlib import Path

# Add MediVoiceAI directory to sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent / "MediVoiceAI"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Import Flask app instance
from app import app, init_database

# WSGI compatibility alias for Vercel Serverless
handler = app
