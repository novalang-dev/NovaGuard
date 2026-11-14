# -*- coding: utf-8 -*-
import os
import hashlib
import subprocess
from core.database import db
from core.heuristic_scanner import HeuristicScanner
from core.config import CHUNK_SIZE

class RiskEngine:
    def __init__(self):
        self.heuristic = HeuristicScanner()

    def calculate_sha256(self, path):
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    def is_signed(self, path):
        try:
            cmd = f"powershell -NoProfile -Command \"(Get-AuthenticodeSignature '{path}').Status -eq 'Valid'\""
            res = subprocess.run(cmd, capture_output=True, text=True, creationflags=0x08000000)
            return "True" in res.stdout
        except Exception:
            return False

    def analyze(self, path):
        if not os.path.isfile(path): 
            return 0, ["Dosya değil"]
        
        # 1. ÖNBELLEK KONTROLÜ (Çok hızlı geçiş)
        try:
            last_mod = os.path.getmtime(path)
            sha = self.calculate_sha256(path)
            
            if sha and db.check_cache(path, sha, last_mod):
                return 0, ["Önbellekten (Temiz)"]
        except Exception:
            sha = None

        # 2. İmza Kontrolü
        if sha:
            sig_hit = db.get_signature(sha)
            if sig_hit:
                return 100, [f"Bilinen Virüs: {sig_hit[0]}"]

        # 3. Sezgisel & İsim Kontrolü
        score, reasons = self.heuristic.evaluate_file(path)
        
        # 4. Dijital İmza Kontrolü
        if path.lower().endswith((".exe", ".dll")):
            if not self.is_signed(path):
                score += 20
                reasons.append("Dijital İmza Yok")
            else:
                score = max(0, score - 20)

        # 5. Temizse Önbelleğe Kaydet
        if score == 0 and sha:
            db.add_to_cache(path, sha, last_mod)

        return min(score, 100), reasons

risk_engine = RiskEngine()