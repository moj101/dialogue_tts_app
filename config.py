# -*- coding: utf-8 -*-
"""
تنظیمات ثابت برنامه.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
TEMP_DIR = DATA_DIR / "temp"
DB_PATH = DATA_DIR / "app_data.db"

DEFAULT_BASE_URL = "https://api.avalai.ir/v1"
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"

AVAILABLE_LANGUAGES = [
    ("fr", "فرانسوی"),
    ("en", "انگلیسی"),
    ("fa", "فارسی"),
    ("de", "آلمانی"),
    ("ar", "عربی"),
]

AVAILABLE_AUDIO_FORMATS = ["mp3", "wav"]

AVAILABLE_VOICES = [
    "alloy",
    "ash",
    "coral",
    "echo",
    "fable",
    "nova",
    "onyx",
    "sage",
    "shimmer",
]