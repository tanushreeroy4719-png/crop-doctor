import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", 8)) * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    MODEL_PATH = os.path.join(BASE_DIR, "model", "crop_doctor_model.keras")
    CLASS_INDEX_PATH = os.path.join(BASE_DIR, "model", "class_indices.json")
    IMG_SIZE = (224, 224)

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    ANTHROPIC_MODEL = "claude-sonnet-4-6"

    HISTORY_PATH = os.path.join(BASE_DIR, "data", "history.json")
