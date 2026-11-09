"""Central configuration. Every path can be overridden with an environment variable."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    DATA_DIR = Path(os.environ.get("HA_DATA_DIR", BASE_DIR / "data"))
    UPLOAD_DIR = Path(os.environ.get("HA_UPLOAD_DIR", BASE_DIR / "uploads"))
    MODEL_DIR = Path(os.environ.get("HA_MODEL_DIR", BASE_DIR / "models"))
    DB_PATH = Path(os.environ.get("HA_DB_PATH", BASE_DIR / "healthcare.db"))
    DEFAULT_DATASET = "mtsamples.csv"          # looked up inside DATA_DIR
    AUTO_REGISTER_DEFAULT = True
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024      # 50 MB upload limit
    MAX_ROWS = 200_000
    MIN_ROWS = 20
    CORS_ORIGINS = os.environ.get(
        "HA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    JSON_SORT_KEYS = False
