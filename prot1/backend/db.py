"""
db.py — SQLite Database Setup
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator

DB_PATH = "resumeiq.db"


# -------------------------------
# INIT DATABASE
# -------------------------------
def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email       TEXT UNIQUE NOT NULL,
                name        TEXT,
                education   TEXT,
                experience  TEXT,
                target_role TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email       TEXT,
                job_title        TEXT,
                company          TEXT,
                ats_score        REAL,
                keyword_match    REAL,
                skill_match      REAL,
                experience_match REAL,
                formatting_score REAL,
                template_used    TEXT,
                resume_url       TEXT,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email)
            );

            CREATE TABLE IF NOT EXISTS keywords (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                keyword     TEXT,
                matched     INTEGER DEFAULT 0,
                FOREIGN KEY (analysis_id) REFERENCES analyses(id)
            );
        """)


# -------------------------------
# DB CONNECTION HANDLER
# -------------------------------
@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -------------------------------
# SAVE ANALYSIS
# -------------------------------
def save_analysis(
    user_email: str,
    job_title: str,
    company: str,
    analysis_data: dict,
    template: str,
    resume_url: str
) -> int:

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO analyses (
                user_email,
                job_title,
                company,
                ats_score,
                keyword_match,
                skill_match,
                experience_match,
                formatting_score,
                template_used,
                resume_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_email,
            job_title,
            company,
            float(analysis_data.get("ats_score", 0)),
            float(analysis_data.get("keyword_match", 0)),
            float(analysis_data.get("skill_match", 0)),
            float(analysis_data.get("experience_match", 0)),
            float(analysis_data.get("formatting_score", 0)),
            template,
            resume_url,
        ))

        analysis_id = cursor.lastrowid or 0

        # Save matched keywords
        for kw in analysis_data.get("matched_keywords", []):
            conn.execute(
                "INSERT INTO keywords (analysis_id, keyword, matched) VALUES (?, ?, 1)",
                (analysis_id, kw)
            )

        # Save missing keywords
        for kw in analysis_data.get("missing_keywords", []):
            conn.execute(
                "INSERT INTO keywords (analysis_id, keyword, matched) VALUES (?, ?, 0)",
                (analysis_id, kw)
            )

        return int(analysis_id)