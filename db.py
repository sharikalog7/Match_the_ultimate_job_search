# db.py
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    company TEXT,
    location TEXT,
    url TEXT UNIQUE,
    description TEXT,
    sponsorship_flag TEXT,
    diagnostic TEXT,
    h1b_history TEXT,
    verified INTEGER DEFAULT 0,
    created_at TEXT
);
"""

class JobDB:
    def __init__(self, path: str = "jobs.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._ensure_schema()

    def _ensure_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def insert_job(self, title, company, location, url, description,
                   sponsorship_flag, diagnostic, h1b_history):
        now = datetime.utcnow().isoformat()
        try:
            self.conn.execute(
                "INSERT INTO jobs (title, company, location, url, description, sponsorship_flag, diagnostic, h1b_history, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, company, location, url, description, sponsorship_flag, str(diagnostic), str(h1b_history), now)
            )
            self.conn.commit()
            return True
        except Exception as e:
            # likely a duplicate URL unique constraint
            return False

    def list_jobs(self) -> List[Dict]:
        cur = self.conn.execute("SELECT id, title, company, location, url, sponsorship_flag, h1b_history, verified, created_at FROM jobs ORDER BY created_at DESC")
        rows = cur.fetchall()
        keys = [d[0] for d in cur.description]
        out = []
        for r in rows:
            out.append(dict(zip(keys, r)))
        return out

    def get_job(self, job_id: int):
        cur = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cur.fetchone()
        if not row:
            return None
        keys = [d[0] for d in cur.description]
        return dict(zip(keys, row))

    def mark_verified(self, job_id: int):
        self.conn.execute("UPDATE jobs SET verified = 1 WHERE id = ?", (job_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
