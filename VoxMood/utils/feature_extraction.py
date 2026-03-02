"""
VoxMood - Feature Extraction Module
Extracts audio features: MFCC, Chroma, Mel Spectrogram, RMS, ZCR
Falls back to hash-based pseudo-features if librosa is unavailable.
"""

import numpy as np
import tempfile
import os

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


def extract_features(audio_path: str, sample_rate: int = 22050) -> np.ndarray:
    """
    Extract comprehensive audio features from an audio file.

    Returns:
        Feature vector as numpy array (116 features)
    """
    if not LIBROSA_AVAILABLE:
        return _fallback_features(audio_path)

    try:
        y, sr = librosa.load(audio_path, sr=sample_rate, mono=True)
        if len(y) < sr:
            y = np.pad(y, (0, sr - len(y)), mode='constant')

        features = []

        # 1. MFCC — 40 × 2 = 80
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        features.extend(np.mean(mfccs, axis=1))
        features.extend(np.std(mfccs, axis=1))

        # 2. Chroma — 12 × 2 = 24
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features.extend(np.mean(chroma, axis=1))
        features.extend(np.std(chroma, axis=1))

        # 3. Mel Spectrogram — 2
        mel = librosa.feature.melspectrogram(y=y, sr=sr)
        features.append(np.mean(mel))
        features.append(np.std(mel))

        # 4. RMS — 2
        rms = librosa.feature.rms(y=y)
        features.append(np.mean(rms))
        features.append(np.std(rms))

        # 5. ZCR — 2
        zcr = librosa.feature.zero_crossing_rate(y)
        features.append(np.mean(zcr))
        features.append(np.std(zcr))

        # 6. Spectral Centroid — 2
        sc = librosa.feature.spectral_centroid(y=y, sr=sr)
        features.append(np.mean(sc))
        features.append(np.std(sc))

        # 7. Spectral Bandwidth — 2
        sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        features.append(np.mean(sb))
        features.append(np.std(sb))

        # 8. Spectral Rolloff — 2
        ro = librosa.feature.spectral_rolloff(y=y, sr=sr)
        features.append(np.mean(ro))
        features.append(np.std(ro))

        return np.array(features)  # 116 features

    except Exception as e:
        raise ValueError(f"Feature extraction failed: {str(e)}")


def _fallback_features(audio_path: str) -> np.ndarray:
    """Generate reproducible pseudo-features when librosa is unavailable."""
    import hashlib
    try:
        with open(audio_path, 'rb') as f:
            data = f.read(8192)
        seed = int(hashlib.md5(data).hexdigest()[:8], 16) % (2**31)
    except Exception:
        seed = 42
    rng = np.random.RandomState(seed)
    return rng.randn(116).astype(np.float32)


def extract_waveform_data(audio_path: str, num_points: int = 200) -> list:
    """Extract downsampled waveform data for visualization."""
    if not LIBROSA_AVAILABLE:
        import hashlib
        with open(audio_path, 'rb') as f:
            raw = f.read()
        seed = int(hashlib.md5(raw[:256]).hexdigest()[:8], 16) % (2**31)
        rng = np.random.RandomState(seed)
        t = np.linspace(0, 4 * np.pi, num_points)
        wave = rng.randn(num_points) * 0.3 + 0.5 * np.sin(t) * np.sin(t * 0.3)
        return wave.tolist()

    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    step = max(1, len(y) // num_points)
    return y[::step][:num_points].tolist()


def extract_spectrogram_data(audio_path: str) -> dict:
    """Extract spectrogram data for visualization."""
    if not LIBROSA_AVAILABLE:
        rng = np.random.RandomState(42)
        D = rng.randn(50, 50)
        return {"data": D.tolist(), "shape": D.shape}

    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    D_small = D[::4, ::4]
    return {"data": D_small.tolist(), "shape": D_small.shape}


def extract_segment_features(audio_path: str, segment_duration: float = 2.0) -> list:
    """Split audio into segments and extract features per segment."""
    if not LIBROSA_AVAILABLE:
        return [_fallback_features(audio_path) for _ in range(3)]

    import soundfile as sf

    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    segment_samples = int(segment_duration * sr)
    segments = []

    for start in range(0, len(y), segment_samples):
        segment = y[start:start + segment_samples]

        # Skip very short segments
        if len(segment) < sr * 0.5:
            continue

        # Pad if needed
        if len(segment) < segment_samples:
            segment = np.pad(segment, (0, segment_samples - len(segment)))

        # ── Windows-safe temp file handling ──────────────────────
        # Use mktemp() so file is never locked when we delete it
        tmp_path = tempfile.mktemp(suffix='.wav')
        try:
            sf.write(tmp_path, segment, sr)
            features = extract_features(tmp_path)
            segments.append(features)
        except Exception:
            pass
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    return segments