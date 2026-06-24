# -*- coding: utf-8 -*-
"""
ابزارهای ساده مربوط به فایل‌های صوتی.

نکات:
1. برای mp3 ادغام باینری بدون ffmpeg انجام می‌شود.
2. برای wav از wave استفاده می‌شود.
3. هشدارهای pydub/ffmpeg ساکت شده‌اند تا کنسول تمیز بماند.
"""

import os
import sys
import wave
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import List


warnings.filterwarnings(
    "ignore",
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work",
    category=RuntimeWarning,
)

warnings.filterwarnings(
    "ignore",
    message="Couldn't find ffprobe or avprobe - defaulting to ffprobe, but may not work",
    category=RuntimeWarning,
)

from pydub import AudioSegment  # noqa: E402


def merge_mp3_files_binary(audio_files: List[str], output_file: str):
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "wb") as outfile:
        for file_path in audio_files:
            path = Path(file_path)
            if not path.exists():
                continue
            with open(path, "rb") as infile:
                outfile.write(infile.read())


def merge_wav_files_native(audio_files: List[str], output_file: str):
    if not audio_files:
        raise ValueError("هیچ فایل wav برای ادغام وجود ندارد.")

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data_chunks = []
    params = None

    for file_path in audio_files:
        path = Path(file_path)
        if not path.exists():
            continue

        with wave.open(str(path), "rb") as wav_in:
            current_params = wav_in.getparams()

            if params is None:
                params = current_params
            else:
                if current_params[:4] != params[:4]:
                    raise ValueError("مشخصات فایل‌های wav یکسان نیست و ادغام ممکن نیست.")

            data_chunks.append(wav_in.readframes(wav_in.getnframes()))

    if params is None:
        raise ValueError("هیچ فایل wav معتبری پیدا نشد.")

    with wave.open(str(out_path), "wb") as wav_out:
        wav_out.setparams(params)
        for chunk in data_chunks:
            wav_out.writeframes(chunk)


def merge_audio_files_with_pydub(audio_files: List[str], output_file: str):
    ffmpeg_exists = shutil.which("ffmpeg")
    ffprobe_exists = shutil.which("ffprobe")

    if not ffmpeg_exists or not ffprobe_exists:
        raise RuntimeError(
            "برای این فرمت، ffmpeg/ffprobe روی سیستم نصب نیست. "
            "فعلاً از mp3 یا wav استفاده کنید."
        )

    AudioSegment.converter = ffmpeg_exists
    AudioSegment.ffprobe = ffprobe_exists

    combined = AudioSegment.empty()

    for file_path in audio_files:
        path = Path(file_path)
        if path.exists():
            segment = AudioSegment.from_file(path)
            combined += segment

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = out_path.suffix.lower().replace(".", "")
    combined.export(out_path, format=fmt)


def merge_audio_files(audio_files: List[str], output_file: str):
    cleaned_files = []
    for file_path in audio_files:
        if file_path and Path(file_path).exists():
            cleaned_files.append(file_path)

    if not cleaned_files:
        raise ValueError("هیچ فایل صوتی معتبری برای ادغام وجود ندارد.")

    ext = Path(output_file).suffix.lower()

    if ext == ".mp3":
        merge_mp3_files_binary(cleaned_files, output_file)
        return

    if ext == ".wav":
        merge_wav_files_native(cleaned_files, output_file)
        return

    merge_audio_files_with_pydub(cleaned_files, output_file)


def open_audio_file(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"فایل پیدا نشد: {file_path}")

    if sys.platform.startswith("win"):
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)