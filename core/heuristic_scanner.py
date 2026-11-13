# -*- coding: utf-8 -*-
"""Katman 2: Kalıp tabanlı sezgisel tarama."""
import os
from core.config import CHUNK_SIZE, MAX_HEURISTIC_SIZE

PATTERNS = {
    b"cmd.exe /c":                  ("Shell komutu", 3),
    b"powershell -enc":             ("Şifreli PowerShell", 4),
    b"powershell -encodedcommand":  ("Şifreli PowerShell", 4),
    b"vssadmin delete shadows":     ("Gölge silme", 5),
    b"reg add hkcu":                ("Registry kalıcılık", 3),
    b"currentversion\\run":         ("Başlangıç kaydı", 3),
    b"autorun.inf":                 ("USB yayılım", 2),
    b"mimikatz":                    ("Kimlik hırsızlığı", 5),
    b"invoke-mimikatz":             ("Mimikatz PS", 5),
    b"nc -e ":                      ("Reverse shell", 5),
    b"netcat -e":                   ("Reverse shell", 5),
    b"downloadstring(":             ("Uzaktan yükleme", 4),
    b"frombase64string(":           ("Base64 gizleme", 3),
}


class HeuristicScanner:
    def scan_file(self, path):
        reasons, max_level = [], 0
        try:
            size = os.path.getsize(path)
            if size == 0 or size > MAX_HEURISTIC_SIZE:
                return (False, [], 0)
            overlap = b""
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    buf = (overlap + chunk).lower()
                    for pat, (desc, lvl) in PATTERNS.items():
                        if pat in buf and desc not in reasons:
                            reasons.append(desc)
                            max_level = max(max_level, lvl)
                    overlap = buf[-64:]
            return (bool(reasons), reasons, max_level)
        except Exception:
            return (False, [], 0)

    def scan_directory(self, root, progress_cb=None):
        findings = []
        files = []
        try:
            for r, _, fs in os.walk(root):
                for f in fs:
                    files.append(os.path.join(r, f))
        except Exception:
            return findings
        total = len(files)
        for i, fp in enumerate(files, 1):
            t, reasons, lvl = self.scan_file(fp)
            if t:
                findings.append({"path": fp, "name": ", ".join(reasons),
                                 "level": lvl, "layer": 2})
            if progress_cb and i % 25 == 0:
                progress_cb(i, total)
        if progress_cb:
            progress_cb(total, total)
        return findings