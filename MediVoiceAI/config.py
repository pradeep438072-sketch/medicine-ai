import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "medivoice-ai-secret-key-default-2026")
    
    # Database Configuration
    # Handles Neon, Supabase, Vercel Postgres, or local SQLite
    raw_db_url = os.getenv("DATABASE_URL", "").strip()
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        
    is_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    
    if raw_db_url:
        SQLALCHEMY_DATABASE_URI = raw_db_url
    elif is_serverless:
        # Vercel Lambda only allows writes to /tmp
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/medivoice.db"
    else:
        # Local development SQLite
        instance_dir = BASE_DIR / "instance"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_dir / 'medivoice.db'}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File uploads: use /tmp in serverless environments to avoid read-only filesystem errors
    if is_serverless:
        UPLOAD_FOLDER = Path("/tmp/uploads")
    else:
        UPLOAD_FOLDER = BASE_DIR / "uploads"
        
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day
    
    # OCR & AI
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

