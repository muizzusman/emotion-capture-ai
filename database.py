import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "emotion_data.db"


def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS emotion_logs (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name            TEXT    NOT NULL,
            timestamp            TEXT    NOT NULL,
            primary_emotion      TEXT    NOT NULL,
            emotion_scores       TEXT,
            ai_analysis          TEXT,
            reflection_questions TEXT,
            image_path           TEXT,
            notes                TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_emotion(user_name, primary_emotion, emotion_scores,
                 ai_analysis, reflection_questions, image_path="", notes=""):
    """Insert one emotion record."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO emotion_logs
            (user_name, timestamp, primary_emotion, emotion_scores,
             ai_analysis, reflection_questions, image_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        primary_emotion,
        json.dumps(emotion_scores),
        ai_analysis,
        reflection_questions,
        image_path,
        notes
    ))
    conn.commit()
    conn.close()


def get_user_history(user_name, limit=30):
    """Return all columns for the history page."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, timestamp, primary_emotion, emotion_scores,
               ai_analysis, reflection_questions, notes, image_path
        FROM emotion_logs
        WHERE user_name = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (user_name, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def get_recent_emotions(user_name, limit=10):
    """Lightweight fetch for AI context — just timestamp + emotion + analysis."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT timestamp, primary_emotion, ai_analysis
        FROM emotion_logs
        WHERE user_name = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (user_name, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def get_emotion_counts(user_name):
    """Return (emotion, count) pairs sorted by frequency."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT primary_emotion, COUNT(*) as cnt
        FROM emotion_logs
        WHERE user_name = ?
        GROUP BY primary_emotion
        ORDER BY cnt DESC
    ''', (user_name,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_total_count(user_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM emotion_logs WHERE user_name = ?', (user_name,))
    count = c.fetchone()[0]
    conn.close()
    return count