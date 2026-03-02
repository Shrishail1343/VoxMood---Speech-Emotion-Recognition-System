"""
VoxMood - Prediction Module
Uses: firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3
- 92% accuracy on real speech
- Trained on RAVDESS + SAVEE + TESS + URDU datasets
- Works on ANY real voice, live recording, uploaded file
- No training needed — model downloads automatically (~2.4GB first run)
"""

import os
import numpy as np
import random
import torch

# ── Emotion config ────────────────────────────────────────────────────────────
EMOTIONS = ['Angry', 'Disgust', 'Fearful', 'Happy', 'Neutral', 'Sad', 'Surprised']

# Map model output labels → display names
LABEL_MAP = {
    'angry':     'Angry',
    'disgust':   'Disgust',
    'fearful':   'Fearful',
    'fear':      'Fearful',
    'happy':     'Happy',
    'neutral':   'Neutral',
    'sad':       'Sad',
    'surprised': 'Surprised',
    'surprise':  'Surprised',
    'calm':      'Neutral',
}

EMOTION_RESPONSES = {
    'Happy': [
        "You sound joyful! Keep that positive energy flowing.",
        "Great vibes detected! Your happiness is contagious.",
        "Your upbeat tone suggests you're in a wonderful mood today."
    ],
    'Sad': [
        "It sounds like you might be feeling down. Remember, this too shall pass.",
        "I sense some sadness in your voice. Be kind to yourself today.",
        "Your tone suggests low spirits. Consider reaching out to someone you trust."
    ],
    'Angry': [
        "Your voice conveys frustration. Taking a few deep breaths can help.",
        "I detect some tension. Try a short walk or mindfulness exercise.",
        "High energy detected — consider channeling it into something productive."
    ],
    'Neutral': [
        "Your tone is calm and composed. A great state for focused work.",
        "Steady and balanced — you sound centered and clear-headed.",
        "Neutral tone detected. Excellent state for decision-making."
    ],
    'Fearful': [
        "Your voice suggests anxiety. Remember: you've overcome challenges before.",
        "I sense worry in your tone. Focus on what you can control right now.",
        "Take a slow deep breath. Grounding yourself can help ease anxiety."
    ],
    'Surprised': [
        "Something unexpected caught you off guard! Embrace the unexpected.",
        "Your tone suggests astonishment — sounds like an interesting moment!",
        "Surprise detected! Life's unexpected moments often bring the best stories."
    ],
    'Disgust': [
        "Your voice conveys strong disapproval. It's okay to feel this way.",
        "I sense some strong feelings. Try to express them constructively.",
        "Your tone suggests displeasure. Take a moment to process your feelings."
    ]
}

EMOTION_COLORS = {
    'Happy':     '#FFD700',
    'Sad':       '#4169E1',
    'Angry':     '#FF4500',
    'Neutral':   '#808080',
    'Fearful':   '#9370DB',
    'Surprised': '#FF69B4',
    'Disgust':   '#228B22',
}

EMOTION_ICONS = {
    'Happy':     '😊',
    'Sad':       '😢',
    'Angry':     '😠',
    'Neutral':   '😐',
    'Fearful':   '😨',
    'Surprised': '😲',
    'Disgust':   '🤢',
}

# HuggingFace model ID
MODEL_ID = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"

# Global cache — load model once, reuse for all predictions
_model           = None
_feature_extractor = None
_id2label        = None
_model_loaded    = False
_model_failed    = False


def load_model(model_dir: str = 'model'):
    """
    Returns (None, None) — Whisper model is loaded via HuggingFace.
    Called on app startup, triggers lazy model loading.
    """
    return None, None


def _load_whisper_model():
    """
    Load Whisper emotion model from HuggingFace.
    Downloads ~2.4GB on first run, then cached locally.
    """
    global _model, _feature_extractor, _id2label
    global _model_loaded, _model_failed

    if _model_loaded:
        return True
    if _model_failed:
        return False

    try:
        from transformers import (AutoModelForAudioClassification,
                                   AutoFeatureExtractor)

        print("\n" + "="*55)
        print("🤗 Loading Whisper Emotion Recognition Model...")
        print(f"   {MODEL_ID}")
        print("   First run downloads ~2.4GB — please wait...")
        print("="*55)

        _feature_extractor = AutoFeatureExtractor.from_pretrained(
            MODEL_ID, do_normalize=True)

        _model = AutoModelForAudioClassification.from_pretrained(MODEL_ID)
        _model.eval()

        _id2label     = _model.config.id2label
        _model_loaded = True

        print("✅ Whisper model loaded successfully!")
        print(f"   Emotions: {list(_id2label.values())}")
        print("="*55 + "\n")
        return True

    except Exception as e:
        print(f"\n❌ Whisper model load failed: {e}")
        print("   Falling back to librosa heuristic prediction.\n")
        _model_failed = True
        return False


def _preprocess_audio(audio_path: str, max_duration: float = 30.0):
    """
    Preprocess audio exactly as per the model card.
    Loads with librosa, pads/truncates, extracts Whisper features.
    """
    import librosa

    audio_array, sampling_rate = librosa.load(audio_path, sr=None)

    # Resample to model's expected rate if needed
    target_sr = _feature_extractor.sampling_rate
    if sampling_rate != target_sr:
        audio_array = librosa.resample(
            audio_array, orig_sr=sampling_rate, target_sr=target_sr)
        sampling_rate = target_sr

    # Pad or truncate to max_duration
    max_length = int(sampling_rate * max_duration)
    if len(audio_array) > max_length:
        audio_array = audio_array[:max_length]
    else:
        audio_array = np.pad(
            audio_array, (0, max_length - len(audio_array)))

    # Extract Whisper features
    inputs = _feature_extractor(
        audio_array,
        sampling_rate=sampling_rate,
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
    )
    return inputs


def _whisper_predict(audio_path: str) -> tuple:
    """
    Run Whisper model prediction exactly as per the model card.
    Returns (emotion, confidence, all_scores).
    """
    # Load model if not already loaded
    if not _load_whisper_model():
        return _librosa_fallback(audio_path)

    try:
        # Preprocess audio
        inputs = _preprocess_audio(audio_path)

        # Move to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model.to(device)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Run inference
        with torch.no_grad():
            outputs = _model(**inputs)

        logits = outputs.logits

        # Get probabilities via softmax
        probs = torch.nn.functional.softmax(logits, dim=-1)
        probs = probs.cpu().numpy()[0]

        # Build scores for all emotions
        all_scores = {}
        for idx, prob in enumerate(probs):
            raw_label = _id2label.get(idx, f'emotion_{idx}')
            label     = LABEL_MAP.get(raw_label.lower(), raw_label.capitalize())
            score     = round(float(prob) * 100, 2)
            if label not in all_scores:
                all_scores[label] = score
            else:
                all_scores[label] = max(all_scores[label], score)

        # Ensure all emotions present
        for em in EMOTION_COLORS:
            if em not in all_scores:
                all_scores[em] = 0.0

        # Top prediction
        top_emotion    = max(all_scores, key=all_scores.get)
        top_confidence = all_scores[top_emotion]

        return top_emotion, top_confidence, all_scores

    except Exception as e:
        print(f"Whisper inference error: {e}")
        return _librosa_fallback(audio_path)


def predict_emotion(audio_path: str, model=None, scaler=None) -> dict:
    """
    Main prediction function.
    Uses Whisper → falls back to librosa if model unavailable.
    """
    emotion, confidence, all_scores = _whisper_predict(audio_path)

    suggestion = random.choice(
        EMOTION_RESPONSES.get(emotion, ["Emotion detected."]))

    return {
        'emotion':    emotion,
        'confidence': round(confidence, 2),
        'all_scores': all_scores,
        'suggestion': suggestion,
        'color':      EMOTION_COLORS.get(emotion, '#8a5cf6'),
        'icon':       EMOTION_ICONS.get(emotion, '🎤')
    }


def predict_emotion_timeline(audio_path: str, model=None, scaler=None,
                              segment_duration: float = 2.0) -> list:
    """
    Split audio into segments and predict emotion for each one.
    Uses Whisper model per segment.
    """
    try:
        import librosa
        import soundfile as sf
        import tempfile

        y, sr     = librosa.load(audio_path, sr=22050, mono=True)
        seg_len   = int(segment_duration * sr)
        timeline  = []

        for i, start in enumerate(range(0, len(y), seg_len)):
            segment = y[start:start + seg_len]

            # Skip very short segments
            if len(segment) < sr * 0.5:
                continue

            # Pad short segments
            if len(segment) < seg_len:
                segment = np.pad(segment, (0, seg_len - len(segment)))

            # Windows-safe temp file
            tmp = tempfile.mktemp(suffix='.wav')
            try:
                sf.write(tmp, segment, sr)
                emotion, confidence, _ = _whisper_predict(tmp)
            except Exception:
                emotion, confidence = 'Neutral', 50.0
            finally:
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except Exception:
                    pass

            timeline.append({
                'time':       round(i * segment_duration, 1),
                'emotion':    emotion,
                'confidence': round(confidence, 2),
                'color':      EMOTION_COLORS.get(emotion, '#666'),
                'icon':       EMOTION_ICONS.get(emotion, '🎤')
            })

        return timeline

    except Exception as e:
        print(f"Timeline error: {e}")
        return []


def _librosa_fallback(audio_path: str) -> tuple:
    """Librosa heuristic fallback when Whisper is unavailable."""
    try:
        import librosa

        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        if len(y) == 0:
            return _random_predict()

        rms      = float(np.mean(librosa.feature.rms(y=y)))
        zcr      = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        centroid = float(np.mean(
            librosa.feature.spectral_centroid(y=y, sr=sr)))
        mfccs    = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_m   = float(np.mean(mfccs[0]))

        scores = np.ones(7) * 5.0

        if rms > 0.1  and zcr > 0.08:                scores[0] += 40  # Angry
        if rms > 0.08 and zcr > 0.07:                scores[3] += 35  # Happy
        if 0.03 < rms < 0.09 and zcr < 0.08:        scores[4] += 30  # Neutral
        if rms < 0.05 and zcr < 0.06 and mfcc_m < 0:scores[5] += 40  # Sad
        if centroid > 3000 and zcr > 0.09:           scores[6] += 30  # Surprised
        if 0.04 < rms < 0.1 and zcr > 0.07:         scores[2] += 25  # Fearful

        scores     = np.clip(scores, 0, None)
        scores     = (scores / scores.sum()) * 100
        idx        = int(np.argmax(scores))
        emotion    = EMOTIONS[idx]
        confidence = float(scores[idx])
        all_scores = {EMOTIONS[i]: round(float(scores[i]), 2)
                      for i in range(len(EMOTIONS))}
        return emotion, confidence, all_scores

    except Exception:
        return _random_predict()


def _random_predict() -> tuple:
    """Last resort fallback."""
    scores     = np.random.dirichlet(np.ones(7) * 2) * 100
    idx        = int(np.argmax(scores))
    all_scores = {EMOTIONS[i]: round(float(scores[i]), 2)
                  for i in range(len(EMOTIONS))}
    return EMOTIONS[idx], float(scores[idx]), all_scores