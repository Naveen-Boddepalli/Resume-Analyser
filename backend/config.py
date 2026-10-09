"""Runtime configuration (environment variables only; no secrets in code)."""

import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")  # empty -> authentication disabled (local development)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
RATE_LIMIT = os.getenv("RATE_LIMIT", "30/minute")
MAX_RANK_FILES = int(os.getenv("MAX_RANK_FILES", "25"))

# Optional LLM narrative (off by default). The score never depends on it.
ENABLE_LLM_NARRATIVE = os.getenv("ENABLE_LLM_NARRATIVE", "0") == "1"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
