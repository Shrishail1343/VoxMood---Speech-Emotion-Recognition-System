# 🎙️ VoxMood — Speech Emotion Recognition System

> AI-powered speech emotion recognition using **OpenAI Whisper Large v3** + HuggingFace Transformers.
> Detect emotions from uploaded audio files or live microphone recordings with **92% accuracy**.
> 🚀 **Live on HuggingFace Spaces:** https://huggingface.co/spaces/shrishail1343/VoxMood

---

## 🤖 AI Model

VoxMood uses the **`firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3`** model from HuggingFace:

| Property | Details |
|---|---|
| **Model** | `firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3` |
| **Base Architecture** | OpenAI Whisper Large v3 |
| **Model Size** | 2.55 GB |
| **Accuracy** | ~92% on real speech |
| **Trained On** | RAVDESS + SAVEE + TESS + URDU datasets |
| **Downloads/month** | 29,300+ |
| **License** | Apache 2.0 |

> ⚡ The model downloads automatically (~2.55GB) on the **first prediction** and is cached permanently at `C:\Users\<you>\.cache\huggingface\hub\`. All subsequent runs load in 15-30 seconds from cache.

---

## 🎭 Detectable Emotions

| Emotion | Emoji | Color |
|---|---|---|
| Happy | 😊 | Gold `#FFD700` |
| Sad | 😢 | Blue `#4169E1` |
| Angry | 😠 | Red-Orange `#FF4500` |
| Neutral | 😐 | Gray `#808080` |
| Fearful | 😨 | Purple `#9370DB` |
| Surprised | 😲 | Pink `#FF69B4` |
| Disgust | 🤢 | Green `#228B22` |

---

## ✨ Features

- 🎵 **Audio Upload** — WAV, MP3, OGG, FLAC, WEBM, M4A (up to 50MB)
- 🎙️ **Live Recording** — Record directly from microphone with real-time waveform visualizer
- 🤖 **HuggingFace AI** — Pre-trained Whisper Large v3 model, no training required
- 📊 **Visualizations** — Waveform, emotion bar chart, radar chart, timeline chart
- ⏱️ **Emotion Timeline** — Per-segment (2-second) emotion analysis for longer audio
- 💡 **AI Suggestions** — Context-aware response suggestions based on detected emotion
- 💾 **SQLite Database** — All predictions stored with full history
- 📈 **Analytics Dashboard** — Distribution charts, prediction history, filter by emotion
- 📄 **PDF Reports** — Downloadable analysis reports via ReportLab
- 🌑 **Dark Cinematic UI** — Professional dark theme with Syne + DM Sans fonts

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.13, Flask 3.1 |
| **AI Model** | HuggingFace Transformers, Whisper Large v3 |
| **Audio Processing** | librosa 0.11, soundfile |
| **Deep Learning** | PyTorch, torchaudio, openai-whisper |
| **Database** | SQLite3 |
| **PDF Generation** | ReportLab |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **Charts** | Chart.js 4.4 |
| **Fonts** | Syne + DM Sans (Google Fonts) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- pip
- Internet connection (for first-time model download ~2.55GB)

### 1. Clone or Extract Project
```bash
cd "D:\Wipro Project\VoxMood\VoxMood"
```

### 2. Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```cmd
pip install Flask Flask-CORS librosa scikit-learn numpy scipy joblib soundfile matplotlib reportlab Werkzeug
pip install transformers torch torchaudio
```

### 4. Run the App
```cmd
python app.py
```

### 5. Open Browser
```
http://localhost:5000
```

> 🌐 **Or visit the live deployment:** https://huggingface.co/spaces/shrishail1343/VoxMood

> 🕐 **First prediction:** The HuggingFace Whisper model downloads automatically (~2.55GB). This takes 5–10 minutes depending on your internet speed. After that, every prediction loads in 15-30 seconds from cache.

---

## 📁 Project Structure

```
VoxMood/
├── app.py                      ← Flask application (main entry point)
├── requirements.txt            ← Python dependencies
├── README.md                   ← This file
│
├── utils/
│   ├── predict.py              ← HuggingFace emotion prediction (Whisper Large v3)
│   ├── preprocess.py           ← Audio validation, conversion, normalization
│   ├── feature_extraction.py   ← Waveform + spectrogram extraction (librosa)
│   └── database.py             ← SQLite operations (save, query, delete)
│
├── templates/
│   ├── index.html              ← Upload / live recording page
│   ├── result.html             ← Prediction result + charts
│   └── dashboard.html          ← Analytics dashboard
│
├── static/
│   ├── css/style.css           ← Dark cinematic theme
│   └── js/
│       ├── main.js             ← Upload UI, MediaRecorder, live waveform
│       ├── result.js           ← Result page charts (Chart.js)
│       └── dashboard.js        ← Dashboard charts + table filter
│
├── database/
│   └── voxmood.db              ← SQLite database (auto-created on first run)
│
└── model/                      ← Legacy sklearn model directory (not used)
```

---

## 🔄 How It Works

```
User uploads audio / records live
        ↓
Flask /predict route receives file
        ↓
librosa loads + normalizes audio → 22050 Hz WAV
        ↓
HuggingFace Whisper Large v3 processes audio (mel spectrogram)
        ↓
Softmax probabilities → 7 emotion scores
        ↓
Top emotion + confidence saved to SQLite
        ↓
Waveform, charts, timeline rendered in browser
```

---

## 🌐 Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Home page — upload or record audio |
| `/predict` | POST | Run emotion prediction on uploaded audio |
| `/result/<id>` | GET | View prediction result with charts |
| `/dashboard` | GET | Analytics dashboard with history |
| `/report/<id>` | GET | Download PDF report |
| `/delete/<id>` | POST | Delete a prediction record |
| `/api/history` | GET | JSON API — prediction history |

---

## 🗄️ Database Schema

### `predictions` table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-increment primary key |
| `filename` | TEXT | Original audio filename |
| `predicted_emotion` | TEXT | Top detected emotion |
| `confidence` | REAL | Confidence percentage (0–100) |
| `all_scores` | TEXT | JSON of all 7 emotion scores |
| `duration` | REAL | Audio duration in seconds |
| `suggestion` | TEXT | AI-generated suggestion text |
| `timestamp` | DATETIME | When analysis was performed |

### `emotion_timeline` table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-increment primary key |
| `prediction_id` | INTEGER | Foreign key → predictions.id |
| `time_offset` | REAL | Segment start time (seconds) |
| `emotion` | TEXT | Emotion for this segment |
| `confidence` | REAL | Confidence for this segment |

### `viz_data` table
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER | Auto-increment primary key |
| `prediction_id` | INTEGER | Foreign key → predictions.id |
| `waveform` | TEXT | JSON array of waveform points |
| `spectrogram` | TEXT | JSON spectrogram data |
| `timeline` | TEXT | JSON timeline segments |

---

## ⚙️ Configuration

| Setting | Default | Location |
|---|---|---|
| Max upload size | 50 MB | `app.py` |
| Audio sample rate | 22050 Hz | `preprocess.py` |
| Timeline segment | 2 seconds | `predict.py` |
| HuggingFace model | `firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3` | `predict.py` |
| Model cache | `~/.cache/huggingface/hub/` | Automatic |
| Database path | `database/voxmood.db` | `database.py` |
| Upload folder | `static/uploads/` | `app.py` |

---

## 🐛 Troubleshooting

### Analysis keeps failing
```cmd
# Check terminal output for exact error
python app.py
# Then upload and read the [ERROR] lines
```

### Model not downloading
```cmd
# Ensure internet connection, then test manually:
python -c "from transformers import pipeline; pipeline('audio-classification', model='firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3')"
```

### Port 5000 already in use
```cmd
python app.py --port 5001
# Then open http://localhost:5001
```

### WinError 32 (Windows file lock)
Already fixed in `feature_extraction.py` — uses `tempfile.mktemp()` instead of `NamedTemporaryFile`.

### pip install fails on Python 3.13
```cmd
# Install without version pins:
pip install Flask Flask-CORS librosa scikit-learn numpy scipy joblib soundfile matplotlib reportlab Werkzeug transformers torch torchaudio
```

### Live recording not working
- Use **Chrome or Edge** (Firefox has limited MediaRecorder support)
- Allow microphone access when browser asks
- Check that waveform canvas appears after clicking Stop

---

## 📊 Model Performance

The `firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3` model was evaluated on:

| Dataset | Description |
|---|---|
| RAVDESS | Ryerson Audio-Visual Database of Emotional Speech |
| SAVEE | Surrey Audio-Visual Expressed Emotion |
| TESS | Toronto Emotional Speech Set |
| URDU | Urdu Language Emotional Speech Dataset |

**Overall accuracy: ~92%** on held-out test set across 7 emotion classes.

> This IS the highest accuracy model. For a lighter alternative (85%), you can switch to `r-f/wav2vec-english-speech-emotion-recognition` (~360MB) in `utils/predict.py`.

---

## 👨‍💻 Development

### Run in debug mode
```cmd
python app.py
# Flask debug=True is already set — auto-reloads on file save
```

### Reset database
```cmd
del database\voxmood.db
python app.py  # recreates automatically
```

### Switch HuggingFace model
Edit `utils/predict.py` line:
```python
MODEL_ID = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"
# Change to any compatible audio-classification model on HuggingFace
```

---

## 📝 License

MIT License — Free to use, modify, and distribute.

---

## 🙏 Credits

- **HuggingFace** — Transformers library + model hosting
- **firdhokk** — `speech-emotion-recognition-with-openai-whisper-large-v3` model
- **OpenAI** — Whisper Large v3 base architecture
- **librosa** — Audio processing
- **Chart.js** — Interactive visualizations
- **Anthropic Claude** — Project architecture + development assistance

---

*VoxMood © 2026 — Built with ❤️ using Flask + HuggingFace Transformers + OpenAI Whisper Large v3*