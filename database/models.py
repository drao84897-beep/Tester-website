import sqlite3
import json
import os
from datetime import datetime
from config import Config


def get_db_connection():
    """Returns a SQLite connection or configures connection based on DATABASE_URI."""
    uri = Config.DATABASE_URI
    if uri.startswith("sqlite:///"):
        db_path = uri.replace("sqlite:///", "")
    else:
        db_path = os.path.join(Config.BASE_DIR, "webverify.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if not already present."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                normalized_url TEXT,
                domain TEXT,
                score INTEGER NOT NULL,
                classification TEXT NOT NULL,
                hosting TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                report_data TEXT NOT NULL
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON scan_reports(url);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON scan_reports(created_at DESC);")
        conn.commit()


def save_scan(data):
    """Saves a completed scan report into the database."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scan_reports (url, normalized_url, domain, score, classification, hosting, report_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("url", ""),
                data.get("normalized_url", data.get("url", "")),
                data.get("domain", {}).get("domain", ""),
                data.get("score", 0),
                data.get("classification", "NEEDS VERIFICATION"),
                data.get("technology", {}).get("hosting", "Standard Web Hosting"),
                json.dumps(data, ensure_ascii=False),
            ),
        )
        scan_id = cursor.lastrowid
        conn.commit()
        return scan_id


def get_all_scans(limit=50):
    """Retrieves list of past scans ordered by recent."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, url, normalized_url, domain, score, classification, hosting, created_at
            FROM scan_reports
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_scan_by_id(scan_id):
    """Retrieves full scan report by ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, url, normalized_url, domain, score, classification, hosting, created_at, report_data FROM scan_reports WHERE id = ?",
            (scan_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        try:
            res["report_data"] = json.loads(res["report_data"])
        except Exception:
            pass
        return res


def delete_scan(scan_id):
    """Deletes a specific scan report."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scan_reports WHERE id = ?", (scan_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_history():
    """Clears all scan history."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scan_reports")
        conn.commit()
        return True
