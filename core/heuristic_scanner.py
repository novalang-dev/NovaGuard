# -*- coding: utf-8 -*-
import os
from core.config import CHUNK_SIZE, MAX_HEURISTIC_SIZE

PATTERNS = {
    b"cmd.exe /c": (15, "Shell komutu"),
    b"powershell -enc": (25, "Şifreli PowerShell"),
    b"vssadmin delete shadows": (30, "Gölge kopya silme"),
    b"mimikatz": (50, "Kimlik hırsızlığı"),
}

SYSTEM_NAMES = ["svchost.exe", "explorer.exe", "lsass.exe", "winlogon.exe"]
SUSPICIOUS_EXT = [".exe", ".bat", ".vbs", ".ps1"]
DOUBLE_EXT = [".pdf.exe", ".jpg.exe", ".txt.bat", ".doc.exe", ".pdf.bat"]

class HeuristicScanner:
    def evaluate_file(self, path, original_sha256=None):
        """Dosyayı inceler ve (Risk Skoru, Sebepler) döndürür."""
        score = 0
        reasons = []
        filename = os.path.basename(path).lower()

        # 1. İsim Analizi (Gizlenme)
        if any(filename.endswith(ext) for ext in DOUBLE_EXT):
            score += 40
            reasons.append("Çift Uzantı Gizlemesi")
        
        if filename in SYSTEM_NAMES and "\\windows\\" not in path.lower():
            score += 35
            reasons.append("Sistem Dosyası Taklidi")
            
        if filename.startswith(".") and filename.endswith((".exe", ".bat")):
            score += 20
            reasons.append("Gizli Dosya Uzantısı")

        # 2. İçerik Analizi (Sezgisel)
        try:
            size = os.path.getsize(path)
            if 0 < size < MAX_HEURISTIC_SIZE:
                overlap = b""
                with open(path, "rb") as f:
                    while True:
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk: break
                        buf = (overlap + chunk).lower()
                        for pat, (pts, desc) in PATTERNS.items():
                            if pat in buf and desc not in reasons:
                                score += pts
                                reasons.append(desc)
                        overlap = buf[-64:]
        except: pass

        return min(score, 100), reasons # Skor maksimum 100 olabilir