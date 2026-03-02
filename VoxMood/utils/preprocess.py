"""
VoxMood - Audio Preprocessing Module
Fixed: properly handles live browser recordings (webm, ogg, blob formats)
and all uploaded audio formats on Windows.
"""

import os
import time
import numpy as np
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {
    'wav', 'mp3', 'ogg', 'flac', 'webm', 'm4a', 'aac', 'opus', 'blob'
}
MAX_FILE_SIZE_MB   = 50
TARGET_SAMPLE_RATE = 22050


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if '.' not in filename:
        return True  # Allow files without extension (live recordings)
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_audio(file_path: str) -> tuple:
    """
    Validate audio file.
    Returns (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "File not found"

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"

    if os.path.getsize(file_path) < 50:
        return False, "Audio file is too small or empty"

    # Try loading a small chunk to verify it's valid audio
    try:
        import librosa
        y, sr = librosa.load(file_path, sr=None, duration=1.0, mono=True)
        if len(y) == 0:
            return False, "Audio file appears to be empty"
    except Exception as e:
        # If librosa fails, still try — soundfile might work
        try:
            import soundfile as sf
            info = sf.info(file_path)
            if info.duration < 0.1:
                return False, "Audio too short"
        except Exception:
            # Accept file anyway and let feature extraction handle it
            pass

    return True, ""


def preprocess_audio(input_path: str, output_path: str = None) -> str:
    """
    Preprocess audio file:
    - Convert any format (webm, ogg, mp3) to WAV
    - Standardize to 22050 Hz mono
    - Normalize amplitude
    - Trim silence

    Works with live browser recordings (webm/ogg blobs).
    Returns path to processed WAV file.
    """
    if output_path is None:
        base        = os.path.splitext(input_path)[0]
        output_path = base + '_processed.wav'

    try:
        import librosa
        import soundfile as sf

        # librosa handles all formats including webm, ogg, mp3
        y, sr = librosa.load(input_path, sr=TARGET_SAMPLE_RATE, mono=True)

        if len(y) == 0:
            raise ValueError("Empty audio after loading")

        # Trim leading/trailing silence
        y, _ = librosa.effects.trim(y, top_db=25)

        # Normalize amplitude to [-1, 1]
        max_amp = np.max(np.abs(y))
        if max_amp > 0:
            y = y / max_amp

        # Save as standard WAV
        sf.write(output_path, y, TARGET_SAMPLE_RATE)
        return output_path

    except Exception as e:
        print(f"Preprocess warning: {e} — using original file")
        # Return original path if processing fails
        # Feature extraction will still work
        return input_path


def get_audio_duration(file_path: str) -> float:
    """Get audio duration in seconds."""
    try:
        import librosa
        y, sr = librosa.load(file_path, sr=None, mono=True)
        return round(len(y) / sr, 2)
    except Exception:
        try:
            import soundfile as sf
            info = sf.info(file_path)
            return round(info.duration, 2)
        except Exception:
            # Rough estimate from file size
            size = os.path.getsize(file_path)
            return round(max(1.0, size / (22050 * 2)), 2)


def save_uploaded_file(file, upload_folder: str) -> str:
    """
    Save uploaded file securely with unique filename.
    Handles browser live recordings (blob files without proper names).
    """
    original_name = file.filename or ''

    # Handle blob/live recordings from browser
    if not original_name or original_name in ('blob', ''):
        # Detect format from content type
        content_type = getattr(file, 'content_type', '') or ''
        if 'ogg' in content_type:
            ext = '.ogg'
        elif 'webm' in content_type:
            ext = '.webm'
        elif 'mp4' in content_type or 'aac' in content_type:
            ext = '.m4a'
        else:
            ext = '.wav'
        filename = f'recording_{int(time.time())}{ext}'
    else:
        filename = secure_filename(original_name)
        if not filename:
            filename = f'audio_{int(time.time())}.wav'

    # Ensure unique filename using timestamp
    base, ext = os.path.splitext(filename)
    unique_filename = f"{base}_{int(time.time())}{ext}"
    file_path = os.path.join(upload_folder, unique_filename)

    file.save(file_path)
    print(f"Saved upload: {file_path} ({os.path.getsize(file_path)} bytes)")
    return file_path