# -*- coding: utf-8 -*-
"""MalwareBazaar full.csv toplu import (tek seferlik)."""
import csv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SignatureDB


def import_full(csv_path):
    db = SignatureDB()
    batch = []
    total = 0
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            sha = (row.get("sha256_hash") or "").strip().lower()
            name = row.get("signature") or row.get("file_type") or "Unknown"
            if len(sha) == 64:
                batch.append((sha, f"Bazaar.{name}", 3))
            if len(batch) >= 1000:
                total += db.add_many(batch)
                batch = []
    if batch:
        total += db.add_many(batch)
    print(f"[Import] {total} imza eklendi. DB toplam: {db.count()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python tools/import_bazaar.py full.csv")
    else:
        import_full(sys.argv[1])