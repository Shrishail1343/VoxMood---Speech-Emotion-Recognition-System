"""
VoxMood - Debug Script
Run this to find exactly what's failing.

Usage:
    python debug_test.py
"""

import os
import sys
import numpy as np

print("=" * 50)
print("VoxMood Debug Test")
print("=" * 50)

# ── Test 1: Imports ───────────────────────────────
print("\n[1] Testing imports...")
try:
    import flask
    print(f"    ✅ Flask {flask.__version__}")
except Exception as e:
    print(f"    ❌ Flask: {e}")

try:
    import librosa
    print(f"    ✅ librosa {librosa.__version__}")
except Exception as e:
    print(f"    ❌ librosa: {e}")

try:
    import sklearn
    print(f"    ✅ scikit-learn {sklearn.__version__}")
except Exception as e:
    print(f"    ❌ scikit-learn: {e}")

try:
    import soundfile
    print(f"    ✅ soundfile {soundfile.__version__}")
except Exception as e:
    print(f"    ❌ soundfile: {e}")

try:
    import joblib
    print(f"    ✅ joblib {joblib.__version__}")
except Exception as e:
    print(f"    ❌ joblib: {e}")

# ── Test 2: Model files ───────────────────────────
print("\n[2] Checking model files...")
if os.path.exists("model/emotion_model.pkl"):
    print("    ✅ emotion_model.pkl found")
else:
    print("    ❌ emotion_model.pkl MISSING — run: python train_model.py --synthetic")

if os.path.exists("model/scaler.pkl"):
    print("    ✅ scaler.pkl found")
else:
    print("    ❌ scaler.pkl MISSING")

# ── Test 3: Load model ────────────────────────────
print("\n[3] Loading model...")
try:
    import joblib
    model  = joblib.load("model/emotion_model.pkl")
    scaler = joblib.load("model/scaler.pkl")
    print(f"    ✅ Model loaded: {type(model).__name__}")
    print(f"    ✅ Model classes: {list(model.classes_)}")
    print(f"    ✅ Scaler expects: {scaler.n_features_in_} features")
except Exception as e:
    print(f"    ❌ Model load failed: {e}")
    sys.exit(1)

# ── Test 4: Feature extraction ────────────────────
print("\n[4] Testing feature extraction...")
try:
    import librosa
    import numpy as np
    from utils.feature_extraction import extract_features

    # Use librosa's built-in test audio
    y, sr = librosa.load(librosa.ex('trumpet'), duration=3.0)

    import tempfile, soundfile as sf
    tmp = tempfile.mktemp(suffix='.wav')
    sf.write(tmp, y, sr)

    features = extract_features(tmp)
    print(f"    ✅ Features extracted: {len(features)} features")
    print(f"    ✅ Feature range: [{features.min():.2f}, {features.max():.2f}]")

    if os.path.exists(tmp):
        os.remove(tmp)

except Exception as e:
    print(f"    ❌ Feature extraction failed: {e}")
    import traceback
    traceback.print_exc()

# ── Test 5: Full prediction pipeline ─────────────
print("\n[5] Testing full prediction pipeline...")
try:
    import librosa
    import soundfile as sf
    import tempfile
    from utils.feature_extraction import extract_features
    from utils.predict import predict_emotion, EXPECTED_FEATURES

    # Create test audio
    y, sr = librosa.load(librosa.ex('trumpet'), duration=3.0)
    tmp = tempfile.mktemp(suffix='.wav')
    sf.write(tmp, y, sr)

    result = predict_emotion(tmp, model, scaler)
    print(f"    ✅ Prediction: {result['emotion']} ({result['confidence']:.1f}%)")
    print(f"    ✅ All scores: {result['all_scores']}")

    if os.path.exists(tmp):
        os.remove(tmp)

except Exception as e:
    print(f"    ❌ Prediction failed: {e}")
    import traceback
    traceback.print_exc()

# ── Test 6: Feature dimension match ──────────────
print("\n[6] Checking feature dimension match...")
try:
    from utils.predict import EXPECTED_FEATURES
    n_model = scaler.n_features_in_
    print(f"    Model expects:     {n_model} features")
    print(f"    predict.py expects:{EXPECTED_FEATURES} features")

    if n_model == EXPECTED_FEATURES:
        print(f"    ✅ Dimensions match!")
    else:
        print(f"    ❌ MISMATCH! Model={n_model}, Code={EXPECTED_FEATURES}")
        print(f"    FIX: Delete model files and retrain:")
        print(f"         del model\\emotion_model.pkl")
        print(f"         del model\\scaler.pkl")
        print(f"         python train_model.py --synthetic")
except Exception as e:
    print(f"    ❌ Check failed: {e}")

# ── Test 7: Database ──────────────────────────────
print("\n[7] Testing database...")
try:
    from utils.database import init_db, save_prediction, get_prediction_by_id
    init_db()
    print("    ✅ Database initialized")

    # Test save and retrieve
    pid = save_prediction(
        filename="debug_test.wav",
        emotion="Happy",
        confidence=85.5,
        all_scores={"Happy": 85.5, "Sad": 5.0},
        duration=3.0,
        suggestion="Test"
    )
    pred = get_prediction_by_id(pid)
    print(f"    ✅ Save & retrieve works (id={pid})")

except Exception as e:
    print(f"    ❌ Database failed: {e}")
    import traceback
    traceback.print_exc()

# ── Test 8: File upload simulation ───────────────
print("\n[8] Simulating file upload...")
try:
    import librosa, soundfile as sf, tempfile
    from utils.preprocess import validate_audio, preprocess_audio, get_audio_duration

    # Create a test WAV file
    y, sr = librosa.load(librosa.ex('trumpet'), duration=3.0)
    test_path = os.path.join('static', 'uploads', 'debug_test.wav')
    os.makedirs('static/uploads', exist_ok=True)
    sf.write(test_path, y, sr)

    is_valid, msg = validate_audio(test_path)
    print(f"    ✅ Validation: {is_valid} {msg}")

    processed = preprocess_audio(test_path)
    print(f"    ✅ Preprocessed: {processed}")

    duration = get_audio_duration(processed)
    print(f"    ✅ Duration: {duration}s")

    # Clean up
    for f in [test_path, processed]:
        if os.path.exists(f) and f != test_path:
            os.remove(f)

except Exception as e:
    print(f"    ❌ Upload simulation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Debug complete! Share output above with Claude.")
print("=" * 50)
