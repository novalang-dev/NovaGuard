# -*- coding: utf-8 -*-
import sqlite3
import threading
import time
from core.config import DB_PATH, HISTORY_DB_PATH

class DatabaseManager:
    _lock = threading.Lock()

    def __init__(self):
        self._init_signatures()
        self._init_history()
        self._init_cache()

    def _connect(self, db_path):
        conn = sqlite3.connect(db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_signatures(self):
        with self._lock:
            conn = self._connect(DB_PATH)
            conn.execute("CREATE TABLE IF NOT EXISTS signatures (sha256 TEXT PRIMARY KEY, name TEXT, level INTEGER)")
            conn.commit()
            conn.close()

    def _init_history(self):
        with self._lock:
            conn = self._connect(HISTORY_DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT, filename TEXT, path TEXT, 
                    threat_name TEXT, risk_score INTEGER, action TEXT
                )
            """)
            conn.commit()
            conn.close()

    def _init_cache(self):
        with self._lock:
            conn = self._connect(HISTORY_DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_cache (
                    file_path TEXT PRIMARY KEY, 
                    file_hash TEXT, 
                    last_modified REAL
                )
            """)
            conn.commit()
            conn.close()

    # --- İmza İşlemleri ---
    def get_signature(self, sha256):
        try:
            conn = self._connect(DB_PATH)
            cur = conn.execute("SELECT name, level FROM signatures WHERE sha256=?", (sha256,))
            row = cur.fetchone()
            conn.close()
            return row
        except: return None

    def add_signatures(self, rows):
        if not rows: return
        with self._lock:
            conn = self._connect(DB_PATH)
            conn.executemany("INSERT OR IGNORE INTO signatures(sha256, name, level) VALUES (?,?,?)", rows)
            conn.commit()
            conn.close()

    # --- Geçmiş İşlemleri ---
    def add_history(self, filename, path, threat_name, risk_score, action):
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            conn = self._connect(HISTORY_DB_PATH)
            conn.execute("INSERT INTO history (time, filename, path, threat_name, risk_score, action) VALUES (?,?,?,?,?,?)",
                         (t, filename, path, threat_name, risk_score, action))
            conn.commit()
            conn.close()

    def get_history(self):
        conn = self._connect(HISTORY_DB_PATH)
        cur = conn.execute("SELECT time, filename, threat_name, risk_score, action FROM history ORDER BY id DESC LIMIT 100")
        rows = cur.fetchall()
        conn.close()
        return rows

    # --- Önbellek İşlemleri ---
    def check_cache(self, file_path, file_hash, last_modified):
        try:
            conn = self._connect(HISTORY_DB_PATH)
            cur = conn.execute("SELECT file_hash FROM scan_cache WHERE file_path=? AND last_modified=?", (file_path, last_modified))
            row = cur.fetchone()
            conn.close()
            return row is not None and row[0] == file_hash
        except: return False

    def add_to_cache(self, file_path, file_hash, last_modified):
        with self._lock:
            try:
                conn = self._connect(HISTORY_DB_PATH)
                conn.execute("INSERT OR REPLACE INTO scan_cache (file_path, file_hash, last_modified) VALUES (?,?,?)", 
                             (file_path, file_hash, last_modified))
                conn.commit()
                conn.close()
            except: pass

    def clear_cache(self):
        with self._lock:
            try:
                conn = self._connect(HISTORY_DB_PATH)
                conn.execute("DELETE FROM scan_cache")
                conn.commit()
                conn.close()
            except: pass

db = DatabaseManager()