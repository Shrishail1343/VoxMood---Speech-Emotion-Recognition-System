# VoxMood – Speech Emotion Recognition System

VoxMood is a full-stack web application that analyzes human emotions from speech audio. The system allows users to upload an audio file or record their voice using the browser microphone, and it predicts the emotional state of the speaker using a pre-trained deep learning model.

The application integrates a HuggingFace transformer model with a Flask backend and a simple web interface built using HTML, CSS, and JavaScript. The goal of the project is to demonstrate how modern speech models can be used in a real web application to perform emotion recognition.

## Emotion Categories

The system predicts the following emotions from speech audio:

* Happy
* Sad
* Angry
* Neutral
* Fearful
* Surprised
* Disgust

These emotions are predicted based on acoustic features learned by the transformer model during training.

## Model Used

The application uses a pre-trained HuggingFace model:

`r-f/wav2vec-english-speech-emotion-recognition`

Model details:

* Architecture: Wav2Vec2
* Model size: approximately 360 MB
* Framework: PyTorch
* Training datasets: RAVDESS, SAVEE, and TESS
* Average accuracy: around 85% on speech emotion classification tasks

The model is automatically downloaded the first time the application runs. After that, it is cached locally and loaded directly from the HuggingFace cache directory.

## Main Features

The system provides several features for analyzing speech emotion:

* Upload audio files for emotion prediction
* Record audio directly from the browser microphone
* Emotion prediction using a transformer-based speech model
* Visualization of waveform and emotion probabilities
* Emotion timeline analysis for longer recordings
* Storage of prediction results in a SQLite database
* Dashboard showing previous predictions and emotion distribution
* Option to generate a PDF report of the analysis results

## Technology Stack

Backend:

* Python
* Flask
* HuggingFace Transformers
* PyTorch
* Librosa for audio processing

Frontend:

* HTML
* CSS
* JavaScript
* Chart.js for visualization

Database:

* SQLite

Additional libraries:

* ReportLab for PDF generation
* Soundfile for handling audio files

## Installation and Setup

Before running the project, make sure Python 3.10 or newer is installed.

Clone or extract the project and navigate to the project folder.

```
cd VoxMood
```

Create a virtual environment:

```
python -m venv venv
```

Activate the virtual environment.

On Windows:

```
venv\Scripts\activate
```

Install the required dependencies:

```
pip install Flask Flask-CORS librosa scikit-learn numpy scipy joblib soundfile matplotlib reportlab Werkzeug
pip install transformers torch torchaudio
```

Run the application:

```
python app.py
```

Open a browser and go to:

```
http://localhost:5000
```

During the first run, the model will download automatically (about 360MB). After the initial download, the model loads instantly from the local cache.

## Project Structure

```
VoxMood
│
├── app.py
├── requirements.txt
│
├── utils
│   ├── predict.py
│   ├── preprocess.py
│   ├── feature_extraction.py
│   └── database.py
│
├── templates
│   ├── index.html
│   ├── result.html
│   └── dashboard.html
│
├── static
│   ├── css
│   │   └── style.css
│   └── js
│       ├── main.js
│       ├── result.js
│       └── dashboard.js
│
└── database
    └── voxmood.db
```

## How the System Works

1. The user uploads an audio file or records speech through the browser.
2. The Flask backend receives the audio file.
3. The audio is processed and normalized using Librosa.
4. The processed audio is passed to the Wav2Vec2 emotion classification model.
5. The model produces probability scores for each emotion class.
6. The emotion with the highest probability is selected as the prediction.
7. The result is stored in the SQLite database.
8. The frontend displays charts and visualizations of the prediction results.

## Database

The application stores prediction results in a SQLite database.

The main table stores information such as:

* uploaded filename
* predicted emotion
* confidence score
* audio duration
* timestamp

Additional tables store visualization data and timeline predictions for longer recordings.

## Model Performance

The emotion recognition model was trained using several public speech emotion datasets including RAVDESS, SAVEE, and TESS. The model achieves roughly 85% accuracy on general speech emotion recognition tasks.

## Possible Improvements

Some possible future improvements for this project include:

* adding multilingual emotion recognition
* improving accuracy using additional datasets
* real-time streaming emotion detection
* deploying the system using a cloud GPU environment
* building a REST API for external applications

## Author

Shrishail S Balikayi
New Horizon College of Engineering