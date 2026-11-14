# -*- coding: utf-8 -*-
"""VirusTotal sorgusu - manuel sağ tık için."""
import requests
from core.config import VT_API_KEY
from core.risk_engine import risk_engine


def check_virustotal(file_path):
    if not VT_API_KEY or VT_API_KEY == "BURAYA_VIRUSTOTAL_API_KEY_YAZILACAK":
        return "❌ Hata: config.py içine VT_API_KEY yazmalısın.\n" \
               "Ücretsiz key: https://www.virustotal.com/gui/my-apikey"

    try:
        sha = risk_engine.calculate_sha256(file_path)
        url = f"https://www.virustotal.com/api/v3/files/{sha}"
        headers = {"x-apikey": VT_API_KEY}
        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code == 200:
            data = r.json()
            stats = data["data"]["attributes"]["last_analysis_stats"]
            mal = stats.get("malicious", 0)
            total = sum(stats.values())
            return f"🦠 VirusTotal Sonucu:\n\n" \
                   f"Dosya: {file_path.split(chr(92))[-1]}\n" \
                   f"Hash: {sha}\n\n" \
                   f"Zararlı bulan: {mal} / {total} antivirüs\n" \
                   f"Durum: {'TEHLİKELİ' if mal > 0 else 'TEMİZ'}"
        elif r.status_code == 404:
            return f"ℹ️ Bu dosya VirusTotal'de yok.\n\nHash: {sha}\n\n" \
                   f"Yani hiçbir antivirüs bunu görmemiş. Yeni bir dosya olabilir."
        else:
            return f"❌ API Hatası: {r.status_code}\nKey geçersiz olabilir."
    except Exception as e:
        return f"❌ Bağlantı Hatası: {e}"