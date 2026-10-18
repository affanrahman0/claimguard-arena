"""Central configuration. Everything comes from environment variables or a .env file."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        val = value.strip().strip('"').strip("'")
        k = key.strip()
        if k not in os.environ:
            os.environ[k] = val


_load_dotenv()

DB_PATH = Path(os.getenv("DB_PATH", str(ROOT / "data" / "claims.db")))
RESULTS_DIR = ROOT / "evaluator" / "results"

# LLM settings. LLM_MODE: auto (Gemini if credentials exist, else mock) | mock | gemini
LLM_MODE = os.getenv("LLM_MODE", "auto").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes")
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_FAST = os.getenv("MODEL_FAST", "gemini-3.8-flash")
MODEL_REASON = os.getenv("MODEL_REASON", "gemini-3.8-flash")

# Risk thresholds: score < INVESTIGATE -> fast_track; <= ESCALATE -> investigate; else escalate
THRESH_INVESTIGATE = 30
THRESH_ESCALATE = 60
