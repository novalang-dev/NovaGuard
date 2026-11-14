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
        """Windows dosyasının dijital imzası var mı kontrol eder."""
        try:
            # PowerShell ile imza kontrolü
            cmd = f"powershell -NoProfile -Command \"(Get-AuthenticodeSignature '{path}').Status -eq 'Valid'\""
            
            # creationflags=0x08000000 (CREATE_NO_WINDOW) -> Siyah CMD penceresini gizler
            res = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                creationflags=0x08000000 
            )
            return "True" in res.stdout
        except Exception:
            return False

    def analyze(self, path):
        """Dosyayı tüm katmanlardan geçirip nihai Risk Skorunu döndürür."""
        if not os.path.isfile(path): 
            return 0, ["Dosya değil"]
        
        # 1. İmza Kontrolü
        sha = self.calculate_sha256(path)
        if sha:
            sig_hit = db.get_signature(sha)
            if sig_hit:
                return 100, [f"Bilinen Virüs: {sig_hit[0]}"]

        # 2. Sezgisel & İsim Kontrolü
        score, reasons = self.heuristic.evaluate_file(path)
        
        # 3. Dijital İmza Kontrolü (Sadece EXE'ler için)
        if path.lower().endswith((".exe", ".dll")):
            if not self.is_signed(path):
                score += 20
                reasons.append("Dijital İmza Yok")
            else:
                score = max(0, score - 20) # İmzalıysa risk düşür

        return min(score, 100), reasons

risk_engine = RiskEngine()