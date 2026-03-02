"""
VoxMood - Main Flask App
Fixed: full error printing to terminal so we can see exactly what fails
"""

import os
import json
import traceback
from flask import (Flask, render_template, request, redirect,
                   url_for, jsonify, send_file, flash)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'voxmood-secret-2024'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('database', exist_ok=True)
os.makedirs('model', exist_ok=True)

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'webm', 'm4a', 'aac'}

# ── Load database ─────────────────────────────────────────────────────────────
from utils.database import (init_db, save_prediction, save_timeline,
                             get_all_predictions, get_prediction_by_id,
                             get_emotion_distribution, get_recent_predictions_for_chart,
                             delete_prediction, save_viz_data, get_viz_data)
init_db()

# ── Load predict module ───────────────────────────────────────────────────────
from utils.predict import (predict_emotion, predict_emotion_timeline,
                            load_model, EMOTION_COLORS)

model, scaler = load_model('model')

EMOTION_COLORS_DEFAULT = {
    'Happy':    '#FFD700',
    'Sad':      '#4169E1',
    'Angry':    '#FF4500',
    'Neutral':  '#808080',
    'Fear':     '#9370DB',
    'Fearful':  '#9370DB',
    'Surprise': '#FF69B4',
    'Surprised':'#FF69B4',
    'Disgust':  '#228B22',
}

def allowed_file(filename):
    if '.' not in filename:
        return True
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    stats = get_emotion_distribution()
    total = sum(stats.values())
    return render_template('index.html', stats=stats, total=total)


@app.route('/predict', methods=['POST'])
def predict():
    print("\n" + "="*60)
    print("PREDICT ROUTE CALLED")
    print("="*60)

    # ── Step 1: Check file in request ─────────────────────────────
    print(f"[1] Files in request: {list(request.files.keys())}")
    print(f"[1] Form data: {dict(request.form)}")

    if 'audio' not in request.files:
        print("[ERROR] No 'audio' key in request.files")
        flash('No audio file received. Please try again.', 'error')
        return redirect(url_for('index'))

    file = request.files['audio']
    print(f"[2] Filename: '{file.filename}'")
    print(f"[2] Content type: '{file.content_type}'")

    if not file or file.filename == '':
        print("[ERROR] Empty filename")
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    # ── Step 2: Save file ──────────────────────────────────────────
    try:
        import time
        filename = file.filename or 'recording'
        if '.' not in filename:
            # Live recording — detect format from content type
            ct = file.content_type or ''
            if 'ogg' in ct:
                ext = '.ogg'
            elif 'webm' in ct:
                ext = '.webm'
            elif 'wav' in ct:
                ext = '.wav'
            else:
                ext = '.wav'
            filename = f'recording_{int(time.time())}{ext}'
        else:
            filename = secure_filename(filename)
            base, ext = os.path.splitext(filename)
            filename = f'{base}_{int(time.time())}{ext}'

        raw_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(raw_path)
        size = os.path.getsize(raw_path)
        print(f"[3] Saved to: {raw_path} ({size} bytes)")

        if size < 100:
            print("[ERROR] File too small")
            flash('Audio file is empty. Please record or upload again.', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        print(f"[ERROR] Save failed: {e}")
        traceback.print_exc()
        flash(f'Could not save file: {str(e)}', 'error')
        return redirect(url_for('index'))

    # ── Step 3: Convert to WAV ─────────────────────────────────────
    try:
        import librosa
        import soundfile as sf
        import numpy as np

        print(f"[4] Loading audio with librosa...")
        y, sr = librosa.load(raw_path, sr=22050, mono=True)
        print(f"[4] Audio loaded: {len(y)} samples, {sr}Hz, {len(y)/sr:.1f}s")

        if len(y) == 0:
            flash('Audio file appears empty. Please try again.', 'error')
            return redirect(url_for('index'))

        # Normalize
        max_amp = np.max(np.abs(y))
        if max_amp > 0:
            y = y / max_amp

        # Save as clean WAV
        processed_path = raw_path.replace(ext, '_processed.wav')
        sf.write(processed_path, y, sr)
        duration = round(len(y) / sr, 2)
        print(f"[4] Processed WAV saved: {processed_path}, duration={duration}s")

    except Exception as e:
        print(f"[ERROR] Audio processing failed: {e}")
        traceback.print_exc()
        # Try using raw file directly
        processed_path = raw_path
        duration = 3.0

    # ── Step 4: Extract waveform for visualization ─────────────────
    try:
        from utils.feature_extraction import extract_waveform_data, extract_spectrogram_data
        waveform    = extract_waveform_data(processed_path, num_points=200)
        spectrogram = extract_spectrogram_data(processed_path)
        print(f"[5] Waveform extracted: {len(waveform)} points")
    except Exception as e:
        print(f"[WARN] Waveform extraction failed: {e}")
        waveform    = []
        spectrogram = {'data': []}

    # ── Step 5: Predict emotion ────────────────────────────────────
    try:
        print(f"[6] Running emotion prediction on: {processed_path}")
        result = predict_emotion(processed_path, model, scaler)
        print(f"[6] Prediction result: {result['emotion']} ({result['confidence']}%)")
        print(f"[6] All scores: {result['all_scores']}")
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        traceback.print_exc()
        flash(f'Prediction error: {str(e)}', 'error')
        return redirect(url_for('index'))

    # ── Step 6: Timeline prediction ────────────────────────────────
    try:
        print(f"[7] Running timeline prediction...")
        timeline = predict_emotion_timeline(processed_path, model, scaler)
        print(f"[7] Timeline: {len(timeline)} segments")
    except Exception as e:
        print(f"[WARN] Timeline failed: {e}")
        timeline = []

    # ── Step 7: Save to database ───────────────────────────────────
    try:
        pred_id = save_prediction(
            filename=os.path.basename(raw_path),
            emotion=result['emotion'],
            confidence=result['confidence'],
            all_scores=result['all_scores'],
            duration=duration,
            suggestion=result['suggestion']
        )
        print(f"[8] Saved to DB with id={pred_id}")

        if timeline:
            save_timeline(pred_id, timeline)

        save_viz_data(pred_id, {
            'waveform':    waveform,
            'spectrogram': spectrogram.get('data', []),
            'timeline':    timeline
        })

    except Exception as e:
        print(f"[ERROR] DB save failed: {e}")
        traceback.print_exc()
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('index'))

    print(f"[9] SUCCESS — redirecting to /result/{pred_id}")
    print("="*60 + "\n")
    return redirect(url_for('result', pred_id=pred_id))


@app.route('/result/<int:pred_id>')
def result(pred_id):
    prediction = get_prediction_by_id(pred_id)
    if not prediction:
        flash('Prediction not found.', 'error')
        return redirect(url_for('index'))

    viz_raw          = get_viz_data(pred_id) or {}
    waveform_data    = viz_raw.get('waveform', [])
    spectrogram_data = viz_raw.get('spectrogram', [])
    timeline_data    = viz_raw.get('timeline', [])

    try:
        all_scores = json.loads(prediction.get('all_scores', '{}'))
    except Exception:
        all_scores = {}

    colors = EMOTION_COLORS if EMOTION_COLORS else EMOTION_COLORS_DEFAULT

    return render_template('result.html',
                           prediction=prediction,
                           all_scores=all_scores,
                           waveform_data=json.dumps(waveform_data),
                           spectrogram_data=json.dumps(spectrogram_data),
                           timeline_data=json.dumps(timeline_data),
                           emotion_colors=json.dumps(colors))


@app.route('/dashboard')
def dashboard():
    predictions  = get_all_predictions(limit=50)
    distribution = get_emotion_distribution()
    recent       = get_recent_predictions_for_chart(limit=20)

    for p in predictions:
        try:
            p['all_scores'] = json.loads(p.get('all_scores', '{}'))
        except Exception:
            p['all_scores'] = {}

    colors = EMOTION_COLORS if EMOTION_COLORS else EMOTION_COLORS_DEFAULT

    return render_template('dashboard.html',
                           predictions=predictions,
                           distribution=json.dumps(distribution),
                           recent=json.dumps(recent),
                           emotion_colors=json.dumps(colors),
                           total=len(predictions))


@app.route('/api/history')
def api_history():
    predictions = get_all_predictions(limit=100)
    return jsonify({'status': 'ok', 'data': predictions})


@app.route('/report/<int:pred_id>')
def generate_report(pred_id):
    prediction = get_prediction_by_id(pred_id)
    if not prediction:
        return jsonify({'error': 'Not found'}), 404
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER
        import tempfile as tf

        all_scores    = json.loads(prediction.get('all_scores', '{}'))
        colors_map    = EMOTION_COLORS if EMOTION_COLORS else EMOTION_COLORS_DEFAULT
        emotion_color = colors_map.get(prediction['predicted_emotion'], '#8a5cf6')
        r = int(emotion_color[1:3], 16) / 255
        g = int(emotion_color[3:5], 16) / 255
        b = int(emotion_color[5:7], 16) / 255

        tmp_path = tf.mktemp(suffix='.pdf')
        doc      = SimpleDocTemplate(tmp_path, pagesize=A4,
                                     rightMargin=inch, leftMargin=inch,
                                     topMargin=inch, bottomMargin=inch)
        styles   = getSampleStyleSheet()
        story    = []

        story.append(Paragraph("VoxMood Analysis Report",
            ParagraphStyle('t', fontSize=24, alignment=TA_CENTER,
                           fontName='Helvetica-Bold',
                           textColor=colors.Color(r, g, b))))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"Detected Emotion: {prediction['predicted_emotion']}",
            ParagraphStyle('r', fontSize=18, alignment=TA_CENTER,
                           fontName='Helvetica-Bold')))
        story.append(Paragraph(
            f"Confidence: {prediction['confidence']:.1f}%", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        meta = [
            ['File',       prediction['filename']],
            ['Timestamp',  prediction['timestamp']],
            ['Duration',   f"{prediction.get('duration', 0):.1f}s"],
            ['Suggestion', prediction.get('suggestion', '')],
        ]
        t = Table(meta, colWidths=[1.5*inch, 4.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(0,-1), colors.lightgrey),
            ('FONTNAME',   (0,0),(0,-1), 'Helvetica-Bold'),
            ('GRID',       (0,0),(-1,-1), 0.5, colors.grey),
            ('PADDING',    (0,0),(-1,-1), 6),
        ]))
        story.append(t)

        if all_scores:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("Score Breakdown", styles['Heading2']))
            rows = [['Emotion','Score (%)']] + [
                [em, f"{sc:.2f}%"]
                for em, sc in sorted(all_scores.items(), key=lambda x:-x[1])
            ]
            st = Table(rows, colWidths=[3*inch, 3*inch])
            st.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0), colors.Color(r,g,b)),
                ('TEXTCOLOR', (0,0),(-1,0), colors.white),
                ('FONTNAME',  (0,0),(-1,0), 'Helvetica-Bold'),
                ('GRID',      (0,0),(-1,-1), 0.5, colors.grey),
                ('PADDING',   (0,0),(-1,-1), 6),
            ]))
            story.append(st)

        doc.build(story)
        return send_file(tmp_path, as_attachment=True,
                         download_name=f'voxmood_{pred_id}.pdf',
                         mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete/<int:pred_id>', methods=['POST'])
def delete(pred_id):
    delete_prediction(pred_id)
    flash('Deleted.', 'success')
    return redirect(url_for('dashboard'))


@app.errorhandler(413)
def too_large(e):
    flash('File too large (max 50MB).', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("🎙️  VoxMood starting...")
    print(f"    Upload folder: {UPLOAD_FOLDER}")
    port = int(os.environ.get('PORT', 7860))
    app.run(debug=False, host='0.0.0.0', port=port)