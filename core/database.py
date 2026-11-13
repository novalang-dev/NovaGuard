# -*- coding: utf-8 -*-
"""SQLite imza veritabanı."""
import sqlite3
import threading
import hashlib
from core.config import DB_PATH


class SignatureDB:
    _lock = threading.Lock()

    def __init__(self, path=DB_PATH):
        self.path = path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS signatures (
                        sha256 TEXT PRIMARY KEY,
                        name   TEXT NOT NULL,
                        level  INTEGER DEFAULT 1
                    )
                """)
                conn.commit()
            except Exception as e:
                print(f"[DB] Init: {e}")
            finally:
                conn.close()

    def add_many(self, rows):
        """rows: [(sha256, name, level), ...] — hızlı toplu ekleme."""
        if not rows:
            return 0
        with self._lock:
            try:
                conn = self._connect()
                conn.executemany(
                    "INSERT OR IGNORE INTO signatures(sha256,name,level) VALUES (?,?,?)",
                    rows
                )
                conn.commit()
                n = conn.total_changes
                conn.close()
                return n
            except Exception as e:
                print(f"[DB] add_many: {e}")
                return 0

    def lookup(self, sha256):
        try:
            conn = self._connect()
            cur = conn.execute(
                "SELECT name, level FROM signatures WHERE sha256=?", (sha256,)
            )
            row = cur.fetchone()
            conn.close()
            return row
        except Exception:
            return None

    def count(self):
        try:
            conn = self._connect()
            n = conn.execute("SELECT COUNT(*) FROM signatures").fetchone()[0]
            conn.close()
            return n
        except Exception:
            return 0


def sha256_of_file(path, chunk_size=4096):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            c = f.read(chunk_size)
            if not c:
                break
            h.update(c)
    return h.hexdigest()