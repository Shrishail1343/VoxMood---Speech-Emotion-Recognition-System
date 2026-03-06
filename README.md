# VoxMood – Speech Emotion Recognition System

VoxMood is a web-based application that analyzes emotions from speech audio. The system allows users to upload an audio file or record speech through the browser microphone. The audio is processed and analyzed using a pretrained deep learning model to predict the emotional state of the speaker.

The project integrates a transformer-based speech model from HuggingFace with a Flask backend and a web interface built using HTML, CSS, and JavaScript. The purpose of the system is to demonstrate how modern speech processing models can be used in a full-stack web application to perform emotion recognition from voice recordings.

A live version of the application is available on HuggingFace Spaces.

Live Demo
https://huggingface.co/spaces/shrishail1343/VoxMood

## Model Used

The system uses the pretrained HuggingFace model:

`firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3`

This model is based on the OpenAI Whisper Large v3 architecture and has been fine-tuned for speech emotion recognition tasks.

Model information:

| Property          | Details                                                          |
| ----------------- | ---------------------------------------------------------------- |
| Model             | firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3 |
| Architecture      | OpenAI Whisper Large v3                                          |
| Model size        | approximately 2.55 GB                                            |
| Accuracy          | around 92%                                                       |
| Training datasets | RAVDESS, SAVEE, TESS, URDU                                       |
| Framework         | PyTorch with HuggingFace Transformers                            |
| License           | Apache 2.0                                                       |

The model is downloaded automatically during the first prediction if it is not already available locally. Once downloaded, it is stored in the HuggingFace cache and loaded from there in subsequent runs.

## Detectable Emotions

The model classifies speech into the following emotion categories:

* Happy
* Sad
* Angry
* Neutral
* Fearful
* Surprised
* Disgust

## Features

The application provides several features for speech emotion analysis:

* Upload audio files for emotion prediction
* Record voice directly from the browser microphone
* Emotion classification using a pretrained Whisper Large v3 model
* Visualization of waveform and emotion probability charts
* Emotion timeline analysis for longer recordings
* Storage of prediction results in a SQLite database
* Dashboard for viewing prediction history and emotion distribution
* Option to generate PDF reports of analysis results

## Technology Stack

Backend
Python
Flask

AI and Audio Processing
HuggingFace Transformers
PyTorch
Librosa
Soundfile

Frontend
HTML
CSS
JavaScript

Visualization
Chart.js

Database
SQLite

Additional Libraries
ReportLab (for generating PDF reports)

## How the System Works

1. The user uploads an audio file or records speech through the browser.
2. The Flask backend receives the audio input.
3. The audio is processed and normalized using Librosa.
4. The processed audio is passed to the Whisper-based emotion classification model.
5. The model generates probability scores for each emotion category.
6. The emotion with the highest probability is selected as the prediction.
7. The result is stored in the SQLite database.
8. The prediction results and visualizations are displayed on the web interface.

## Application Routes

| Route        | Description                                          |
| ------------ | ---------------------------------------------------- |
| /            | Main page for uploading or recording audio           |
| /predict     | Processes uploaded audio and runs emotion prediction |
| /result/<id> | Displays prediction result with charts               |
| /dashboard   | Shows prediction history and statistics              |
| /report/<id> | Generates a downloadable PDF report                  |
| /delete/<id> | Deletes a stored prediction                          |
| /api/history | Returns prediction history as JSON                   |

## Database Schema

### predictions

| Column            | Description                         |
| ----------------- | ----------------------------------- |
| id                | Primary key                         |
| filename          | Name of uploaded audio file         |
| predicted_emotion | Predicted emotion label             |
| confidence        | Confidence score                    |
| all_scores        | Probability scores for all emotions |
| duration          | Length of the audio                 |
| suggestion        | Generated response suggestion       |
| timestamp         | Time of prediction                  |

## Model Performance

The pretrained model used in this project was trained using several public speech emotion datasets including:

* RAVDESS – Ryerson Audio-Visual Database of Emotional Speech
* SAVEE – Surrey Audio-Visual Expressed Emotion dataset
* TESS – Toronto Emotional Speech Set
* URDU Emotional Speech Dataset

## Acknowledgements

HuggingFace for transformer models and hosting services
OpenAI for the Whisper architecture
Librosa for audio processing tools
Chart.js for visualization libraries
Public speech emotion datasets used in model training