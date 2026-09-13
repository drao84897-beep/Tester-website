import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration with sensible production-safe defaults."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "webverify-ai-secure-secret-key-2026")
    BASE_DIR = base_dir

    # Database configuration (SQLite by default, easily configurable to MySQL)
    DATABASE_URI = os.environ.get(
        "DATABASE_URI", f"sqlite:///{base_dir / 'webverify.db'}"
    )

    # Scanner settings
    SCAN_TIMEOUT = int(os.environ.get("SCAN_TIMEOUT", 8))
    MAX_RESPONSE_SIZE = int(os.environ.get("MAX_RESPONSE_SIZE_BYTES", 3 * 1024 * 1024))  # 3 MB
    MAX_CRAWL_PAGES = int(os.environ.get("MAX_CRAWL_PAGES", 10))
    USER_AGENT = os.environ.get(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 WebVerifyAI/1.0",
    )

    # SSRF Protection: Blocked networks and reserved hosts
    BLOCKED_HOSTS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "metadata.google.internal",
        "169.254.169.254",  # AWS/Cloud metadata
    }

    # AI Configuration (strictly optional - system runs full heuristic analysis without keys)
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "none").strip().lower()
    AI_API_KEY = os.environ.get("AI_API_KEY", "").strip()
    AI_MODEL = os.environ.get("AI_MODEL", "").strip()
