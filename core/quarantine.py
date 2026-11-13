# -*- coding: utf-8 -*-
"""Katman 4: Otomatik karantina + yerel ağ onayı."""
import os
import shutil
import time
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from core.config import (QUARANTINE_DIR, APPROVAL_TIMEOUT,
                         MOBILE_SERVER_HOST, MOBILE_SERVER_PORT)

MANIFEST = os.path.join(QUARANTINE_DIR, "manifest.json")


def _load_manifest():
    if not os.path.exists(MANIFEST):
        return {}
    try:
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_manifest(d):
    try:
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[L4] manifest: {e}")


class ApprovalState:
    def __init__(self):
        self.lock = threading.Lock()
        self.pending = None
        self.result = None
        self.event = threading.Event()

    def request(self, reason, timeout=APPROVAL_TIMEOUT):
        with self.lock:
            self.pending = {"reason": reason, "created": time.time()}
            self.result = None
            self.event.clear()
        self.event.wait(timeout)
        with self.lock:
            res = self.result
            self.pending = None
            return res == "approve"

    def submit(self, decision):
        with self.lock:
            if self.pending is None:
                return False
            self.result = decision
            self.event.set()
            return True


HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NovaGuard</title>
<style>
 body{font-family:system-ui;background:#0e1116;color:#e6edf3;
      margin:0;padding:24px;text-align:center}
 .card{background:#161b22;border:1px solid #30363d;border-radius:12px;
       padding:24px;max-width:480px;margin:auto}
 h1{color:#58a6ff;font-size:20px}
 .reason{background:#0d1117;border:1px solid #30363d;border-radius:8px;
         padding:12px;margin:16px 0;word-break:break-word;font-size:14px}
 button{width:100%;padding:14px;margin:6px 0;border:none;border-radius:8px;
        font-size:16px;font-weight:600;cursor:pointer}
 .yes{background:#238636;color:#fff}
 .no{background:#da3633;color:#fff}
 .warn{color:#f0883e;font-size:13px}
</style></head><body><div class="card">
<h1>NovaGuard — Kritik Onay</h1>
<p class="warn">Bu işlem yalnızca cihaz sahibinin onayıyla yapılır.</p>
<div class="reason">__REASON__</div>
<form method="POST" action="/approve">
<button class="yes" type="submit">✔ ONAYLA</button></form>
<form method="POST" action="/deny">
<button class="no" type="submit">✖ REDDET</button></form>
</div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    state = None

    def log_message(self, *a):
        pass

    def _send(self, code, body):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        try:
            self.wfile.write(b)
        except Exception:
            pass

    def do_GET(self):
        if self.state and self.state.pending:
            reason = self.state.pending["reason"]
            safe = reason.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            self._send(200, HTML.replace("__REASON__", safe))
        else:
            self._send(200, "<h2>Bekleyen onay yok.</h2>")

    def do_POST(self):
        ok = False
        if self.path == "/approve":
            ok = self.state.submit("approve") if self.state else False
        elif self.path == "/deny":
            ok = self.state.submit("deny") if self.state else False
        else:
            self._send(404, "Not found")
            return
        self._send(200 if ok else 400,
                   "<h2>Karar iletildi.</h2>" if ok else "<h2>Bekleyen işlem yok.</h2>")


class MobileServer:
    def __init__(self, state):
        self.state = state
        self._httpd = None
        self._thread = None

    def start(self):
        if self._httpd:
            return
        Handler.state = self.state
        try:
            self._httpd = ThreadingHTTPServer(
                (MOBILE_SERVER_HOST, MOBILE_SERVER_PORT), Handler
            )
            self._thread = threading.Thread(
                target=self._httpd.serve_forever, daemon=True,
                name="NovaGuard-MobileServer"
            )
            self._thread.start()
            print(f"[Mobile] http://{MOBILE_SERVER_HOST}:{MOBILE_SERVER_PORT}")
        except OSError as e:
            print(f"[Mobile] başlatılamadı: {e}")

    def stop(self):
        if self._httpd:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception:
                pass
            self._httpd = None


class QuarantineManager:
    def __init__(self, approval):
        self.approval = approval
        self.server = MobileServer(approval)

    def start_server(self): self.server.start()
    def stop_server(self):  self.server.stop()

    def _xor(self, path):
        try:
            with open(path, "r+b") as f:
                while True:
                    c = f.read(4096)
                    if not c:
                        break
                    f.seek(-len(c), 1)
                    f.write(bytes(b ^ 0x5A for b in c))
        except Exception as e:
            print(f"[L4] xor: {e}")

    def quarantine(self, path, name, sha, layer):
        try:
            qpath = os.path.join(
                QUARANTINE_DIR,
                f"{(sha or 'x')[:16]}_{int(time.time())}.qtn"
            )
            shutil.copy2(path, qpath)
            self._xor(qpath)
            try:
                os.remove(path)
            except Exception as e:
                print(f"[L4] silme: {e}")
            m = _load_manifest()
            m[os.path.basename(qpath)] = {
                "original_path": path, "threat": name,
                "sha256": sha, "layer": layer, "at": time.time()
            }
            _save_manifest(m)
            return {"ok": True, "path": qpath}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def restore(self, qname):
        approved = self.approval.request(f"Geri yükleme: {qname}")
        if not approved:
            return {"ok": False, "reason": "rejected/timeout"}
        try:
            qp = os.path.join(QUARANTINE_DIR, qname)
            if not os.path.exists(qp):
                return {"ok": False, "error": "yok"}
            m = _load_manifest()
            meta = m.get(qname)
            if not meta:
                return {"ok": False, "error": "kayıt yok"}
            self._xor(qp)
            dest = meta["original_path"]
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(qp, dest)
            del m[qname]
            _save_manifest(m)
            return {"ok": True, "to": dest}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def disable_protection(self):
        approved = self.approval.request("Koruma KAPATMA isteği")
        return {"ok": approved}

    def list_all(self):
        return _load_manifest()