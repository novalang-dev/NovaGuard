# -*- coding: utf-8 -*-
"""NovaGuard arayüzü."""
import os
import socket
import threading
from tkinter import filedialog

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False
    import tkinter as tk
    from tkinter import ttk

from core.signature_scanner import SignatureScanner
from core.heuristic_scanner import HeuristicScanner
from core.behavioral_shield import BehavioralShield
from core.quarantine import QuarantineManager, ApprovalState
from core.realtime import RealtimeProtector
from core.updater import start_background as start_updater
from core.config import (MOBILE_SERVER_PORT, WATCH_PATHS, QUARANTINE_DIR)
from core.database import SignatureDB


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class NovaGuardUI:
    def __init__(self):
        self.approval = ApprovalState()
        self.qm = QuarantineManager(self.approval)
        self.l1 = SignatureScanner()
        self.l2 = HeuristicScanner()
        self.l3 = BehavioralShield(alert_callback=self._on_behavior_alert)
        self.rt = RealtimeProtector(WATCH_PATHS, self._realtime_scan)
        self.is_scanning = False
        self._build_ui()
        self.qm.start_server()
        self.l3.start()
        self.rt.start()
        start_updater()
        self.log(f"[OK] DB imza sayısı: {SignatureDB().count()}")
        self.log(f"[OK] Onay sunucusu: http://{local_ip()}:{MOBILE_SERVER_PORT}")

    # ---------- UI ----------
    def _build_ui(self):
        if HAS_CTK:
            ctk.set_appearance_mode("dark")
            self.root = ctk.CTk()
            self.root.title("NovaGuard v0.2")
            self.root.geometry("920x640")
            ctk.CTkLabel(self.root, text="🛡️ NovaGuard",
                         font=("Segoe UI", 24, "bold")).pack(pady=6)
            self.status = ctk.CTkLabel(self.root, text="Hazır.")
            self.status.pack(pady=2)
            f = ctk.CTkFrame(self.root); f.pack(pady=6)
            ctk.CTkButton(f, text="📁 Dizini Tara",
                          command=self._ask_scan).grid(row=0, column=0, padx=4)
            ctk.CTkButton(f, text="🔒 Karantina",
                          command=self._show_q).grid(row=0, column=1, padx=4)
            ctk.CTkButton(f, text="♻️ Geri Yükle",
                          command=self._restore).grid(row=0, column=2, padx=4)
            ctk.CTkButton(f, text="⚠️ Korumayı Kapat",
                          command=self._disable,
                          fg_color="#7a2020").grid(row=0, column=3, padx=4)
            ctk.CTkButton(f, text="🔄 İmza Güncelle",
                          command=self._manual_update).grid(row=0, column=4, padx=4)
            self.progress = ctk.CTkProgressBar(self.root, width=820)
            self.progress.set(0); self.progress.pack(pady=6)
            self.log_box = ctk.CTkTextbox(self.root, width=860, height=420,
                                          font=("Consolas", 11))
            self.log_box.pack(pady=6)
        else:
            self.root = tk.Tk()
            self.root.title("NovaGuard v0.2")
            self.root.geometry("920x640")
            self.root.configure(bg="#0e1116")
            tk.Label(self.root, text="🛡️ NovaGuard", fg="#58a6ff",
                     bg="#0e1116", font=("Segoe UI", 20, "bold")).pack(pady=6)
            self.status = tk.Label(self.root, text="Hazır.",
                                   bg="#0e1116", fg="#e6edf3")
            self.status.pack()
            f = tk.Frame(self.root, bg="#0e1116"); f.pack(pady=6)
            tk.Button(f, text="Dizini Tara", command=self._ask_scan).grid(row=0, column=0, padx=4)
            tk.Button(f, text="Karantina", command=self._show_q).grid(row=0, column=1, padx=4)
            tk.Button(f, text="Geri Yükle", command=self._restore).grid(row=0, column=2, padx=4)
            tk.Button(f, text="Korumayı Kapat", command=self._disable,
                      bg="#7a2020", fg="white").grid(row=0, column=3, padx=4)
            tk.Button(f, text="İmza Güncelle",
                      command=self._manual_update).grid(row=0, column=4, padx=4)
            self.progress = ttk.Progressbar(self.root, length=820, mode="determinate")
            self.progress.pack(pady=6)
            self.log_box = tk.Text(self.root, width=110, height=22,
                                   bg="#161b22", fg="#e6edf3",
                                   font=("Consolas", 10), bd=0)
            self.log_box.pack(pady=6)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def log(self, msg):
        def _a():
            try:
                self.log_box.insert("end", msg + "\n")
                self.log_box.see("end")
            except Exception:
                pass
        try:
            self.root.after(0, _a)
        except Exception:
            print(msg)

    def _status(self, t):
        try:
            if HAS_CTK:
                self.status.configure(text=t)
            else:
                self.status.config(text=t)
        except Exception:
            pass

    # ---------- Tarama ----------
    def _ask_scan(self):
        p = filedialog.askdirectory(title="Klasör seç")
        if not p:
            return
        threading.Thread(target=self._scan_dir, args=(p,), daemon=True).start()

    def _prog(self, c, t):
        pct = c / t if t else 0
        def _s():
            try:
                if HAS_CTK:
                    self.progress.set(pct)
                else:
                    self.progress["value"] = pct * 100
            except Exception:
                pass
        try:
            self.root.after(0, _s)
        except Exception:
            pass

    def _scan_dir(self, path):
        if self.is_scanning:
            self.log("[UI] Tarama var.")
            return
        self.is_scanning = True
        self._status("L1 imza taraması...")
        try:
            f1 = self.l1.scan_directory(path, self._prog)
            for f in f1:
                self.log(f"[L1] 🦠 {f['name']} → {f['path']}")
                self._q_file(f)
            self._status("L2 sezgisel tarama...")
            f2 = self.l2.scan_directory(path, self._prog)
            for f in f2:
                self.log(f"[L2] 🦠 {f['name']} → {f['path']}")
                self._q_file(f)
            self.log(f"[UI] ✅ Bitti. Toplam: {len(f1) + len(f2)}")
            self._status(f"Tarama tamam: {len(f1) + len(f2)}")
        except Exception as e:
            self.log(f"[UI] hata: {e}")
        finally:
            self.is_scanning = False

    def _realtime_scan(self, path):
        """Watchdog yeni dosyada çağırır — hızlı tarama + karantina."""
        try:
            t, name, lvl, sha = self.l1.scan_file(path)
            if t:
                self.log(f"[RT-L1] 🦠 {name} → {path}")
                self._q_file({"path": path, "name": name,
                              "sha256": sha, "layer": 1})
                return
            t2, reasons, lvl2 = self.l2.scan_file(path)
            if t2:
                self.log(f"[RT-L2] 🦠 {', '.join(reasons)} → {path}")
                self._q_file({"path": path, "name": ", ".join(reasons),
                              "sha256": sha or "", "layer": 2})
        except Exception as e:
            print(f"[RT] {e}")

    def _q_file(self, f):
        r = self.qm.quarantine(f["path"], f["name"],
                               f.get("sha256") or "", f["layer"])
        if r.get("ok"):
            self.log(f"[L4] 🔒 {r['path']}")
        else:
            self.log(f"[L4] ⚠️ {r.get('error')}")

    # ---------- Davranış ----------
    def _on_behavior_alert(self, e):
        mem = f" | MEM: {e['memory_hits']}" if e.get("memory_hits") else ""
        self.log(f"[L3] ⚠️ PID {e['pid']} ({e['name']}) — {e['reason']}{mem}")

    # ---------- Karantina ----------
    def _show_q(self):
        m = self.qm.list_all()
        self.log("---- KARANTİNA ----")
        if not m:
            self.log("(boş)")
        for k, v in m.items():
            self.log(f"• {k} | {v['threat']} | eski: {v['original_path']}")
        self.log("---------------------")

    def _restore(self):
        m = self.qm.list_all()
        if not m:
            self.log("[UI] Karantina boş.")
            return
        qname = list(m.keys())[0]
        self.log(f"[UI] Onay isteniyor: {qname}")
        threading.Thread(target=self._do_restore, args=(qname,),
                         daemon=True).start()

    def _do_restore(self, qname):
        r = self.qm.restore(qname)
        if r.get("ok"):
            self.log(f"[L4] ✅ Geri yüklendi: {r['to']}")
        else:
            self.log(f"[L4] ❌ {r}")

    def _disable(self):
        threading.Thread(target=self._do_disable, daemon=True).start()

    def _do_disable(self):
        r = self.qm.disable_protection()
        self.log("[L4] ⚠️ Koruma kapandı." if r["ok"]
                 else "[L4] ❌ Kapatma reddedildi.")

    # ---------- Güncelleme ----------
    def _manual_update(self):
        self.log("[UI] İmza güncelleme başladı...")
        threading.Thread(target=self._do_update, daemon=True).start()

    def _do_update(self):
        try:
            from core.updater import update_once
            update_once()
            self.log(f"[UI] ✅ DB toplam: {SignatureDB().count()}")
        except Exception as e:
            self.log(f"[UI] ❌ güncelleme: {e}")

    # ---------- Kapat ----------
    def _on_close(self):
        try:
            self.rt.stop()
            self.l3.stop()
            self.qm.stop_server()
        finally:
            self.root.destroy()

    def run(self):
        self.root.mainloop()