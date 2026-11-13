# -*- coding: utf-8 -*-
"""NovaGuard genel yapılandırma — Win 8.1 uyumlu."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUARANTINE_DIR = os.path.join(BASE_DIR, "quarantine")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "signatures.db")
RECENT_CSV = os.path.join(DATA_DIR, "recent.csv")

CHUNK_SIZE = 4096
MAX_HEURISTIC_SIZE = 5 * 1024 * 1024
BEHAVIOR_INTERVAL = 5
MOBILE_SERVER_HOST = "0.0.0.0"
MOBILE_SERVER_PORT = 5000
APPROVAL_TIMEOUT = 120
UPDATE_INTERVAL_HOURS = 6

# Win 8.1 + Win 10 uyumlu kullanıcı klasörleri
USER_HOME = os.environ.get("USERPROFILE") or os.path.expanduser("~")
WATCH_PATHS = [
    os.path.join(USER_HOME, "Downloads"),
    os.path.join(USER_HOME, "Desktop"),
    os.path.join(USER_HOME, "Documents"),
]

for d in (DATA_DIR, QUARANTINE_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)