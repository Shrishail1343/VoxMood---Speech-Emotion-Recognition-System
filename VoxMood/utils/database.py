"""
VoxMood - Database Module
Handles all SQLite database operations.
Added: save_viz_data / get_viz_data so visualization data is stored
in DB instead of URL params — fixes 414 error and repeated upload issues.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join('database', 'voxmood.db')


def get_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database and create all tables."""
    os.makedirs('database', exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # Main predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            filename          TEXT NOT NULL,
            predicted_emotion TEXT NOT NULL,
            confidence        REAL NOT NULL,
            all_scores        TEXT,
            duration          REAL,
            suggestion        TEXT,
            timestamp         DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Emotion timeline per segment
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emotion_timeline (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER,
            time_offset   REAL,
            emotion       TEXT,
            confidence    REAL,
            FOREIGN KEY (prediction_id) REFERENCES predictions(id)
        )
    ''')

    # ── NEW: Visualization data table ─────────────────────────────────
    # Stores waveform, spectrogram, timeline JSON per prediction
    # This fixes 414 URI Too Long and allows unlimited repeat uploads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS viz_data (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER UNIQUE,
            waveform      TEXT,
            spectrogram   TEXT,
            timeline      TEXT,
            FOREIGN KEY (prediction_id) REFERENCES predictions(id)
        )
    ''')

    conn.commit()
    conn.close()


# ── Predictions ───────────────────────────────────────────────────────────────

def save_prediction(filename: str, emotion: str, confidence: float,
                    all_scores: dict = None, duration: float = 0.0,
                    suggestion: str = '') -> int:
    """Save a prediction result. Returns the new record ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions
            (filename, predicted_emotion, confidence, all_scores,
             duration, suggestion, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        emotion,
        confidence,
        json.dumps(all_scores) if all_scores else '{}',
        duration,
        suggestion,
        datetime.now().isoformat()
    ))
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id


def get_prediction_by_id(pred_id: int) -> Optional[dict]:
    """Get a single prediction by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM predictions WHERE id = ?', (pred_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_predictions(limit: int = 100) -> list:
    """Get all predictions ordered by most recent."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM predictions
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_emotion_distribution() -> dict:
    """Get count of each emotion for dashboard charts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT predicted_emotion, COUNT(*) as count
        FROM predictions
        GROUP BY predicted_emotion
        ORDER BY count DESC
    ''')
    result = {row['predicted_emotion']: row['count']
              for row in cursor.fetchall()}
    conn.close()
    return result


def get_recent_predictions_for_chart(limit: int = 20) -> list:
    """Get recent predictions for the timeline chart."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, predicted_emotion, confidence, timestamp
        FROM predictions
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


def delete_prediction(pred_id: int):
    """Delete a prediction and all related data."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM emotion_timeline WHERE prediction_id = ?', (pred_id,))
    cursor.execute(
        'DELETE FROM viz_data WHERE prediction_id = ?', (pred_id,))
    cursor.execute(
        'DELETE FROM predictions WHERE id = ?', (pred_id,))
    conn.commit()
    conn.close()


# ── Timeline ──────────────────────────────────────────────────────────────────

def save_timeline(prediction_id: int, timeline: list):
    """Save emotion timeline segments for a prediction."""
    conn = get_connection()
    cursor = conn.cursor()
    for entry in timeline:
        cursor.execute('''
            INSERT INTO emotion_timeline
                (prediction_id, time_offset, emotion, confidence)
            VALUES (?, ?, ?, ?)
        ''', (prediction_id, entry['time'],
              entry['emotion'], entry['confidence']))
    conn.commit()
    conn.close()


def get_timeline_by_prediction(pred_id: int) -> list:
    """Get emotion timeline for a specific prediction."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM emotion_timeline
        WHERE prediction_id = ?
        ORDER BY time_offset
    ''', (pred_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ── Visualization Data ────────────────────────────────────────────────────────

def save_viz_data(prediction_id: int, viz: dict):
    """
    Save waveform, spectrogram, and timeline visualization data.
    Uses INSERT OR REPLACE so re-running the same prediction_id is safe.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO viz_data
            (prediction_id, waveform, spectrogram, timeline)
        VALUES (?, ?, ?, ?)
    ''', (
        prediction_id,
        json.dumps(viz.get('waveform', [])),
        json.dumps(viz.get('spectrogram', [])),
        json.dumps(viz.get('timeline', []))
    ))
    conn.commit()
    conn.close()


def get_viz_data(prediction_id: int) -> Optional[dict]:
    """
    Retrieve visualization data for a prediction.
    Returns dict with waveform, spectrogram, timeline keys.
    Returns empty dict if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM viz_data WHERE prediction_id = ?', (prediction_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {}

    return {
        'waveform':    json.loads(row['waveform']    or '[]'),
        'spectrogram': json.loads(row['spectrogram'] or '[]'),
        'timeline':    json.loads(row['timeline']    or '[]'),
    }