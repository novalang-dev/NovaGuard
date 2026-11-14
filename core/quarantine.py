# -*- coding: utf-8 -*-
"""Karantina yöneticisi - dosyaları şifreleyip kilitler."""
import os
import shutil
import time
import json
from core.config import QUARANTINE_DIR

MANIFEST = os.path.join(QUARANTINE_DIR, "manifest.json")


def _load_manifest():
    if not os.path.exists(MANIFEST):
        return {}
    try:
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_manifest(data):
    try:
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[L4] manifest yazılamadı: {e}")


def _xor_inplace(path):
    """Dosyayı XOR ile şifreler (basit ama etkili)."""
    try:
        with open(path, "r+b") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                f.seek(-len(chunk), 1)
                f.write(bytes(b ^ 0x5A for b in chunk))
    except Exception as e:
        print(f"[L4] XOR hatası: {e}")


class Quarantine:
    def quarantine(self, file_path, threat_name, risk_score):
        """Dosyayı karantinaya al."""
        try:
            if not os.path.isfile(file_path):
                return {"ok": False, "error": "Dosya yok"}

            ts = int(time.time())
            base = os.path.basename(file_path)
            qname = f"{base}_{ts}.qtn"
            qpath = os.path.join(QUARANTINE_DIR, qname)

            # 1. Kopyala
            shutil.copy2(file_path, qpath)
            # 2. Şifrele (artık çalıştırılamaz)
            _xor_inplace(qpath)
            # 3. Orijinali sil
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"[L4] Silme hatası: {e}")

            # 4. Manifest'e kaydet
            m = _load_manifest()
            m[qname] = {
                "original_path": file_path,
                "threat": threat_name,
                "risk": risk_score,
                "at": ts
            }
            _save_manifest(m)

            return {"ok": True, "qpath": qpath, "qname": qname}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def restore(self, qname, target_dir=None):
        """Karantinadan geri yükle (şifreyi çöz)."""
        try:
            qpath = os.path.join(QUARANTINE_DIR, qname)
            if not os.path.exists(qpath):
                return {"ok": False, "error": "Karantinada yok"}

            m = _load_manifest()
            meta = m.get(qname)
            if not meta:
                return {"ok": False, "error": "Kayıt yok"}

            # Şifreyi çöz
            _xor_inplace(qpath)

            # Nereye koyacağız?
            if target_dir:
                dest = os.path.join(target_dir, qname.split("_")[0])
            else:
                dest = meta["original_path"]

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(qpath, dest)

            del m[qname]
            _save_manifest(m)
            return {"ok": True, "to": dest}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_all(self):
        return _load_manifest()

    def delete_forever(self, qname):
        """Karantinadaki dosyayı kalıcı sil."""
        try:
            qpath = os.path.join(QUARANTINE_DIR, qname)
            if os.path.exists(qpath):
                os.remove(qpath)
            m = _load_manifest()
            if qname in m:
                del m[qname]
                _save_manifest(m)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}


quarantine = Quarantine()