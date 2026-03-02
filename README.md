# 🎙️ VoxMood — Speech Emotion Recognition System

A production-ready full-stack web application that detects human emotions from audio using machine learning.

---

## ✨ Features

| Feature | Details |
|---|---|
| **6 Emotions** | Happy, Sad, Angry, Neutral, Fear, Surprise |
| **Upload Audio** | WAV, MP3, OGG, FLAC (up to 50MB) |
| **Live Recording** | MediaRecorder API with real-time visualization |
| **Feature Extraction** | MFCC, Chroma, Mel Spectrogram, RMS, ZCR |
| **Visualizations** | Waveform, Radar, Bar, Timeline charts (Chart.js) |
| **AI Insights** | Contextual suggestions based on detected emotion |
| **Emotion Timeline** | Per-segment emotion tracking over audio duration |
| **PDF Reports** | Downloadable analysis reports (ReportLab) |
| **Analytics Dashboard** | History table, distribution charts, timeline |
| **SQLite Database** | Persistent storage of all predictions |

---

## 🗂️ Project Structure

```
VoxMood/
├── app.py                    # Flask application & routes
├── train_model.py            # ML model training pipeline
├── requirements.txt
│
├── model/
│   ├── emotion_model.pkl     # Trained classifier
│   └── scaler.pkl            # Feature scaler
│
├── utils/
│   ├── feature_extraction.py # MFCC, Chroma, Mel, RMS, ZCR
│   ├── preprocess.py         # Audio validation & normalization
│   ├── predict.py            # Inference + response suggestions
│   └── database.py           # SQLite CRUD operations
│
├── static/
│   ├── css/style.css         # Dark cinematic UI
│   ├── js/main.js            # Upload, recording, loading
│   ├── js/result.js          # Result page charts
│   └── js/dashboard.js       # Dashboard analytics charts
│
├── templates/
│   ├── index.html            # Upload + Record page
│   ├── result.html           # Prediction result
│   └── dashboard.html        # Analytics dashboard
│
└── database/
    └── voxmood.db            # SQLite database (auto-created)
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourname/voxmood.git
cd VoxMood

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Train the Model

**Option A — Using RAVDESS dataset (recommended):**
```bash
# Download RAVDESS from https://zenodo.org/record/1188976
# Extract to a folder, then:
python train_model.py --dataset /path/to/RAVDESS
```

**Option B — Synthetic data (instant, for testing):**
```bash
python train_model.py --synthetic
```

This creates `model/emotion_model.pkl` and `model/scaler.pkl`.

> **No model?** The app still works in demo mode using audio feature heuristics.

### 3. Run the App

```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 🎯 API Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Home page — upload or record audio |
| `/predict` | POST | Process audio, run prediction |
| `/result/<id>` | GET | Show prediction result + visualizations |
| `/dashboard` | GET | Analytics dashboard |
| `/api/history` | GET | JSON API — all predictions |
| `/report/<id>` | GET | Download PDF report |
| `/delete/<id>` | POST | Delete a prediction record |

---

## 🔊 Audio Processing Pipeline

```
Input Audio
    ↓
Validate (format, size, integrity)
    ↓
Preprocess (convert to WAV, 22050Hz, mono, normalize)
    ↓
Feature Extraction:
  • MFCC (40 coefficients × mean + std = 80 features)
  • Chroma STFT (12 × mean + std = 24 features)
  • Mel Spectrogram (mean + std = 2 features)
  • RMS Energy (mean + std = 2 features)
  • Zero Crossing Rate (mean + std = 2 features)
  • Spectral Centroid, Bandwidth, Rolloff (6 features)
  = 116 total features
    ↓
StandardScaler normalization
    ↓
GradientBoostingClassifier prediction
    ↓
Confidence scores for all 6 emotions
    ↓
Save to SQLite + return JSON response
```

---

## 🧠 ML Model

The default model uses **Gradient Boosting Classifier** from scikit-learn:

- **Features**: 116-dimensional vector (MFCC + Chroma + spectral)
- **Estimators**: 200 trees
- **Validation**: 80/20 train-test split with stratification
- **Dataset**: RAVDESS (~1440 samples) achieves ~70-85% accuracy

To experiment with other models, edit `train_model.py`:
```python
# Try SVM
from sklearn.svm import SVC
model = SVC(kernel='rbf', C=1.0, probability=True)

# Try Random Forest
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=300)
```

---

## 🗃️ Database Schema

```sql
CREATE TABLE predictions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    filename          TEXT NOT NULL,
    predicted_emotion TEXT NOT NULL,
    confidence        REAL NOT NULL,
    all_scores        TEXT,          -- JSON: {emotion: score, ...}
    duration          REAL,          -- seconds
    suggestion        TEXT,          -- AI response
    timestamp         DATETIME
);

CREATE TABLE emotion_timeline (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id   INTEGER REFERENCES predictions(id),
    time_offset     REAL,
    emotion         TEXT,
    confidence      REAL
);
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `voxmood-secret-2024` | Flask session key |
| `MAX_CONTENT_LENGTH` | 50MB | Max upload size |
| `TARGET_SAMPLE_RATE` | 22050 Hz | Audio normalization rate |

Set via environment:
```bash
export SECRET_KEY="your-secure-key"
python app.py
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| Flask | Web framework |
| librosa | Audio analysis & feature extraction |
| scikit-learn | ML model training & inference |
| numpy | Numerical computing |
| soundfile | Audio I/O |
| joblib | Model serialization |
| reportlab | PDF generation |
| matplotlib | (optional) spectrogram generation |

---

## 🔮 Roadmap

- [ ] TensorFlow/Keras deep learning model option
- [ ] Real-time streaming analysis via WebSocket
- [ ] Multi-speaker diarization
- [ ] Batch file processing
- [ ] REST API with JWT authentication
- [ ] Docker containerization
- [ ] MySQL/PostgreSQL support

---

## 📄 License

MIT License — free for personal and commercial use.

---

*Built with 🎙️ Flask + librosa + scikit-learn + Chart.js*
