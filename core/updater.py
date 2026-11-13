# -*- coding: utf-8 -*-
"""İmza güncelleme — MalwareBazaar recent.csv (offline çalışır)."""
import csv
import os
import threading
import time
import urllib.request
from core.config import RECENT_CSV, UPDATE_INTERVAL_HOURS
from core.database import SignatureDB

AUTH_KEY = os.environ.get("ABUSECH_AUTH_KEY", "")


def _download():
    if not AUTH_KEY:
        print("[Updater] ABUSECH_AUTH_KEY yok, atlandı.")
        return False
    url = f"https://mb-api.abuse.ch/v2/files/exports/{AUTH_KEY}/recent.csv"
    try:
        urllib.request.urlretrieve(url, RECENT_CSV)
        return True
    except Exception as e:
        print(f"[Updater] indirme: {e}")
        return False


def _import():
    if not os.path.exists(RECENT_CSV):
        return 0
    db = SignatureDB()
    rows = []
    try:
        with open(RECENT_CSV, "r", encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                sha = (row.get("sha256_hash") or "").strip().lower()
                name = row.get("signature") or row.get("file_type") or "Unknown"
                if len(sha) == 64:
                    rows.append((sha, f"Bazaar.{name}", 3))
    except Exception as e:
        print(f"[Updater] parse: {e}")
        return 0
    return db.add_many(rows)


def update_once():
    if _download():
        n = _import()
        print(f"[Updater] {n} imza eklendi. Toplam DB: {SignatureDB().count()}")


def start_background():
    def _loop():
        while True:
            try:
                update_once()
            except Exception as e:
                print(f"[Updater] döngü: {e}")
            time.sleep(UPDATE_INTERVAL_HOURS * 3600)
    threading.Thread(target=_loop, daemon=True, name="NovaGuard-Updater").start()