"""
VoxMood - Model Training Script
Fixed: generates better synthetic data that matches real audio feature patterns.
Run this FIRST before starting the app.

Usage:
    python train_model.py --synthetic        # Quick start (no dataset needed)
    python train_model.py --dataset PATH     # Train with real RAVDESS dataset
"""

import os
import sys
import argparse
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Must match feature_extraction.py exactly
EXPECTED_FEATURES = 116
EMOTIONS = ['Angry', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']


def generate_synthetic_data(n_samples_per_class: int = 300):
    """
    Generate realistic synthetic training data.
    Feature layout matches extract_features() output:
        [0:40]   MFCC means
        [40:80]  MFCC stds
        [80:104] Chroma means + stds
        [104]    Mel mean
        [105]    Mel std
        [106]    RMS mean      ← key for energy
        [107]    RMS std
        [108]    ZCR mean      ← key for pitch
        [109]    ZCR std
        [110]    Spectral centroid mean
        [111]    Spectral centroid std
        [112]    Spectral bandwidth mean
        [113]    Spectral bandwidth std
        [114]    Spectral rolloff mean
        [115]    Spectral rolloff std
    """
    print(f"Generating synthetic training data ({n_samples_per_class} samples/class)...")
    np.random.seed(42)
    X, y = [], []

    # Emotion-specific feature profiles based on real speech research
    emotion_profiles = {
        'Angry': {
            'mfcc_mean': (2.0,  8.0),   # high energy MFCCs
            'mfcc_std':  (20.0, 6.0),   # high variance
            'rms':       (0.15, 0.05),  # high energy
            'zcr':       (0.12, 0.03),  # high ZCR
            'centroid':  (3000, 800),   # high pitch
        },
        'Fear': {
            'mfcc_mean': (-2.0, 6.0),
            'mfcc_std':  (18.0, 5.0),
            'rms':       (0.06, 0.03),  # medium-low energy
            'zcr':       (0.09, 0.03),
            'centroid':  (2500, 700),
        },
        'Happy': {
            'mfcc_mean': (3.0,  7.0),   # positive MFCCs
            'mfcc_std':  (15.0, 5.0),
            'rms':       (0.12, 0.04),  # medium-high energy
            'zcr':       (0.10, 0.03),
            'centroid':  (2800, 600),
        },
        'Neutral': {
            'mfcc_mean': (0.0,  5.0),   # neutral MFCCs
            'mfcc_std':  (10.0, 3.0),   # low variance
            'rms':       (0.07, 0.02),  # medium energy
            'zcr':       (0.07, 0.02),
            'centroid':  (2000, 400),
        },
        'Sad': {
            'mfcc_mean': (-4.0, 6.0),   # negative MFCCs
            'mfcc_std':  (8.0,  3.0),   # low variance
            'rms':       (0.04, 0.02),  # low energy
            'zcr':       (0.04, 0.02),  # low ZCR
            'centroid':  (1500, 400),   # low pitch
        },
        'Surprise': {
            'mfcc_mean': (1.0,  9.0),   # variable
            'mfcc_std':  (22.0, 7.0),   # very high variance
            'rms':       (0.13, 0.05),
            'zcr':       (0.11, 0.04),
            'centroid':  (3200, 900),   # very high pitch
        },
    }

    for emotion, profile in emotion_profiles.items():
        for _ in range(n_samples_per_class):
            feat = np.zeros(EXPECTED_FEATURES)

            # MFCC means [0:40]
            feat[0:40] = np.random.normal(
                profile['mfcc_mean'][0],
                profile['mfcc_mean'][1], 40)

            # MFCC stds [40:80]
            feat[40:80] = np.abs(np.random.normal(
                profile['mfcc_std'][0],
                profile['mfcc_std'][1], 40))

            # Chroma [80:104]
            feat[80:104] = np.random.uniform(0.3, 0.8, 24)

            # Mel [104:106]
            feat[104] = abs(np.random.normal(50, 20))
            feat[105] = abs(np.random.normal(30, 10))

            # RMS energy [106:108]
            feat[106] = abs(np.random.normal(
                profile['rms'][0], profile['rms'][1]))
            feat[107] = abs(np.random.normal(
                profile['rms'][1] * 0.5, 0.01))

            # ZCR [108:110]
            feat[108] = abs(np.random.normal(
                profile['zcr'][0], profile['zcr'][1]))
            feat[109] = abs(np.random.normal(
                profile['zcr'][1] * 0.5, 0.005))

            # Spectral centroid [110:112]
            feat[110] = abs(np.random.normal(
                profile['centroid'][0], profile['centroid'][1]))
            feat[111] = abs(np.random.normal(300, 100))

            # Spectral bandwidth [112:114]
            feat[112] = abs(np.random.normal(2000, 500))
            feat[113] = abs(np.random.normal(200, 80))

            # Spectral rolloff [114:116]
            feat[114] = abs(np.random.normal(4000, 1000))
            feat[115] = abs(np.random.normal(500, 150))

            X.append(feat)
            y.append(emotion)

    print(f"✅  Generated {len(X)} samples across {len(emotion_profiles)} emotions")
    return np.array(X), np.array(y)


def load_ravdess_dataset(dataset_path: str):
    """Load RAVDESS dataset and extract real features."""
    import glob

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from utils.feature_extraction import extract_features

    RAVDESS_MAP = {
        '01': 'Neutral', '02': 'Neutral',
        '03': 'Happy',   '04': 'Sad',
        '05': 'Angry',   '06': 'Fear',
        '07': 'Neutral', '08': 'Surprise'
    }

    audio_files = glob.glob(
        os.path.join(dataset_path, '**', '*.wav'), recursive=True)

    if not audio_files:
        print(f"No WAV files found in {dataset_path}")
        print("Falling back to synthetic data...")
        return generate_synthetic_data()

    print(f"Found {len(audio_files)} audio files in RAVDESS dataset")
    X, y = [], []

    for i, path in enumerate(audio_files):
        parts = os.path.basename(path).replace('.wav', '').split('-')
        if len(parts) < 3:
            continue
        emotion = RAVDESS_MAP.get(parts[2])
        if not emotion:
            continue

        try:
            features = extract_features(path)
            features = _fix_feature_length(features)
            X.append(features)
            y.append(emotion)
            if (i + 1) % 100 == 0:
                print(f"  Processed {i+1}/{len(audio_files)}...")
        except Exception as e:
            print(f"  Skipping {os.path.basename(path)}: {e}")

    if len(X) < 50:
        print("Not enough samples from dataset, adding synthetic data...")
        Xs, ys = generate_synthetic_data(n_samples_per_class=100)
        X.extend(Xs.tolist())
        y.extend(ys.tolist())

    return np.array(X), np.array(y)


def _fix_feature_length(features):
    if len(features) == EXPECTED_FEATURES:
        return features
    elif len(features) < EXPECTED_FEATURES:
        return np.pad(features, (0, EXPECTED_FEATURES - len(features)))
    else:
        return features[:EXPECTED_FEATURES]


def train_model(X: np.ndarray, y: np.ndarray, model_dir: str = 'model'):
    """Train and save the emotion recognition model."""
    os.makedirs(model_dir, exist_ok=True)

    print(f"\nDataset: {len(X)} samples, {X.shape[1]} features")
    unique, counts = np.unique(y, return_counts=True)
    print(f"Distribution: {dict(zip(unique, counts))}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    # Scale features
    scaler       = StandardScaler()
    X_train_s    = scaler.fit_transform(X_train)
    X_test_s     = scaler.transform(X_test)

    # Train model
    print("\nTraining Gradient Boosting Classifier...")
    model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        random_state=42,
        verbose=0
    )
    model.fit(X_train_s, y_train)

    # Evaluate
    y_pred   = model.predict(X_test_s)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n✅  Test Accuracy: {accuracy * 100:.1f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save
    model_path  = os.path.join(model_dir, 'emotion_model.pkl')
    scaler_path = os.path.join(model_dir, 'scaler.pkl')
    joblib.dump(model,  model_path)
    joblib.dump(scaler, scaler_path)
    print(f"💾  Model  → {model_path}")
    print(f"💾  Scaler → {scaler_path}")

    return accuracy


def main():
    parser = argparse.ArgumentParser(description='Train VoxMood emotion model')
    parser.add_argument('--dataset',   type=str, default=None,
                        help='Path to RAVDESS dataset folder')
    parser.add_argument('--model-dir', type=str, default='model',
                        help='Directory to save model files')
    parser.add_argument('--synthetic', action='store_true',
                        help='Use synthetic data (no dataset needed)')
    parser.add_argument('--samples',   type=int, default=300,
                        help='Samples per emotion class (default: 300)')
    args = parser.parse_args()

    print("🎙️  VoxMood — Model Training Pipeline")
    print("=" * 45)

    if args.synthetic or args.dataset is None:
        X, y = generate_synthetic_data(n_samples_per_class=args.samples)
    else:
        X, y = load_ravdess_dataset(args.dataset)

    accuracy = train_model(X, y, args.model_dir)
    print(f"\n🎉  Training complete! Accuracy: {accuracy * 100:.1f}%")
    print("\nNow run:  python app.py")


if __name__ == '__main__':
    main()