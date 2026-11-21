import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / "admin.env")
load_dotenv(BASE_DIR / ".env")

def _configured_path(name: str, default: Path) -> Path:
    path = Path(os.getenv(name, str(default)))
    return path if path.is_absolute() else (BASE_DIR / path).resolve()


class Settings(BaseModel):
    # App Settings
    APP_NAME: str = "Automotive AI Assistant"
    DEBUG: bool = True
    
    # Directories
    BASE_DIR: Path = BASE_DIR
    BROCHURES_DIR: Path = _configured_path("BROCHURES_DIR", BASE_DIR.parent / "brochures")
    UPLOAD_DIR: Path = _configured_path("UPLOAD_DIR", BASE_DIR / "uploads")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    
    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # LLM Settings: "gemini", "openai", or "mock"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Model Names
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "models/gemini-3.8-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
    
    # Embedding Dimension (1536 for OpenAI / Gemini aligned)
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "6"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.25"))

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.BROCHURES_DIR, exist_ok=True)
