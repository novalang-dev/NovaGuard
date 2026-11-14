# -*- coding: utf-8 -*-
"""NovaGuard Ultimate - Modern Arayüz."""
import os
import time
import threading
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw

import customtkinter as ctk

from core.risk_engine import risk_engine
from core.quarantine import quarantine
from core.realtime import RealtimeProtector, State, is_ignored
from core.behavioral import BehavioralShield
from core.database import db
from core.vt_api import check_virustotal
from ui.warning_popup import show_warning


class NovaGuardUI:
    def __init__(self):
        self.is_scanning = False
        self.scan_count = 0
        self.threat_count = 0

        self.behavior = BehavioralShield(alert_callback=self._on_behavior_alert)
        self.rt = RealtimeProtector(self._on_new_file)

        self._build_ui()
        self._start_services()
        self._update_clock()

    # ---------- UI KURULUMU ----------
    def _build_ui(self):
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.title("NovaGuard Ultimate")
        self.root.geometry("1050x720")
        self.root.configure(fg_color="#0a0a0c")

        # ---- HEADER ----
        header = ctk.CTkFrame(self.root, fg_color="transparent", height=70)
        header.pack(fill="x", padx=20, pady=(15, 5))

        # --- YENİ LOGO ÇİZİMİ ---
        logo_img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(logo_img)
        # Neon Mavi Kalkan
        d.polygon([(32, 4), (56, 16), (56, 44), (32, 60), (8, 44), (8, 16)], fill="#00d2ff")
        # Kalkanın içindeki siyah detay
        d.rectangle([28, 20, 36, 44], fill="#0a0a0c")
        d.rectangle([22, 20, 42, 26], fill="#0a0a0c")
        
        # Resmi Tkinter formatına çevir
        self.logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(36, 36))
        
        # Logoyu ve yazıyı ekrana bas
        ctk.CTkLabel(header, image=self.logo_ctk, text="").pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header, text="NovaGuard", font=("Segoe UI", 28, "bold"), text_color="#ffffff").pack(side="left")
        ctk.CTkLabel(header, text="ULTIMATE", font=("Segoe UI", 12, "bold"), text_color="#ffaa00").pack(side="left", padx=10, pady=(10, 0))

        # Sağ üst: Oyun Modu + Saat
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.pack(side="right")

        self.game_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(right_frame, text="🎮 Oyun Modu", variable=self.game_var, command=self._toggle_game, progress_color="#ff8c00", font=("Segoe UI", 12, "bold")).pack(side="left", padx=15)

        self.clock = ctk.CTkLabel(right_frame, text="00:00:00", font=("Consolas", 14, "bold"), text_color="#888899")
        self.clock.pack(side="left", padx=10)

        # ---- DURUM PANELİ ----
        status = ctk.CTkFrame(self.root, fg_color="#121216", corner_radius=12, height=70)
        status.pack(fill="x", padx=20, pady=8)
        status.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(status, text="● Sistem Aktif", font=("Segoe UI", 14, "bold"), text_color="#00ff88")
        self.lbl_status.pack(side="left", padx=20)

        self.lbl_stats = ctk.CTkLabel(status, text="Taranan: 0 | Tehdit: 0", font=("Segoe UI", 12), text_color="#888899")
        self.lbl_stats.pack(side="right", padx=20)

        # ---- SEKMELER ----
        self.tabs = ctk.CTkTabview(self.root, fg_color="#121216", corner_radius=15)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tab_scan = self.tabs.add("📁 Tarama & Loglar")
        self.tab_quar = self.tabs.add("🔒 Karantina")
        self.tab_hist = self.tabs.add("📜 Geçmiş")
        self.tab_settings = self.tabs.add("⚙️ Ayarlar")

        self._build_tab_scan()
        self._build_tab_quarantine()
        self._build_tab_history()
        self._build_tab_settings()

        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)

    def _build_tab_scan(self):
        f = ctk.CTkFrame(self.tab_scan, fg_color="transparent")
        f.pack(fill="x", pady=10)

        ctk.CTkButton(f, text="📁 Dizin Tara", width=140, height=40, fg_color="#0055ff", hover_color="#0044cc", font=("Segoe UI", 13, "bold"), command=self._ask_scan).pack(side="left", padx=5)
        ctk.CTkButton(f, text="📄 Dosya Tara", width=140, height=40, fg_color="#1f1f24", hover_color="#2a2a30", command=self._ask_file_scan).pack(side="left", padx=5)
        ctk.CTkButton(f, text="🌐 VirusTotal (Manuel)", width=180, height=40, fg_color="#6a1b9a", hover_color="#8e24aa", command=self._ask_vt).pack(side="left", padx=5)

        self.progress = ctk.CTkProgressBar(self.tab_scan, height=8, progress_color="#00d2ff")
        self.progress.set(0)
        self.progress.pack(fill="x", pady=8)

        self.log_box = ctk.CTkTextbox(self.tab_scan, font=("Consolas", 12), fg_color="#050505", text_color="#00ff88", border_width=0)
        self.log_box.pack(fill="both", expand=True)

    def _build_tab_quarantine(self):
        top = ctk.CTkFrame(self.tab_quar, fg_color="transparent")
        top.pack(fill="x", pady=10)
        ctk.CTkButton(top, text="🔄 Yenile", width=120, command=self._load_quarantine_list).pack(side="left", padx=5)
        self.quar_list = ctk.CTkScrollableFrame(self.tab_quar, fg_color="#050505")
        self.quar_list.pack(fill="both", expand=True, pady=10)

    def _build_tab_history(self):
        top = ctk.CTkFrame(self.tab_hist, fg_color="transparent")
        top.pack(fill="x", pady=10)
        ctk.CTkButton(top, text="🔄 Yenile", width=120, command=self._load_history).pack(side="left", padx=5)
        self.hist_box = ctk.CTkTextbox(self.tab_hist, font=("Consolas", 11), fg_color="#050505")
        self.hist_box.pack(fill="both", expand=True, pady=10)

    def _build_tab_settings(self):
        ctk.CTkLabel(self.tab_settings, text="İstisna Klasörler (Buralar Taranmaz)", font=("Segoe UI", 14, "bold")).pack(pady=10)
        self.ignore_box = ctk.CTkTextbox(self.tab_settings, height=150, font=("Consolas", 11))
        self.ignore_box.pack(fill="x", padx=20, pady=10)

        from core.config import IGNORE_PATHS
        self.ignore_box.insert("end", "\n".join(IGNORE_PATHS))

        ctk.CTkButton(self.tab_settings, text="💾 Kaydet", fg_color="#238636", hover_color="#2ea043", command=self._save_ignores).pack(pady=10)

        # KALDIRMA BUTONU
        ctk.CTkLabel(self.tab_settings, text="").pack() 
        ctk.CTkButton(self.tab_settings, text="🗑️ NovaGuard'ı Kaldır", fg_color="#da3633", hover_color="#f85149", command=self._uninstall).pack(pady=20)

    # ---------- KALDIRMA İŞLEMİ ----------
    def _uninstall(self):
        cevap = messagebox.askyesno("Kaldır", "NovaGuard'ı kaldırmak istediğinize emin misiniz?\nTüm başlangıç kayıtları silinecek ve koruma kapatılacak.")
        if cevap:
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "NovaGuardUltimate")
                winreg.CloseKey(key)
            except Exception:
                pass
            
            messagebox.showinfo("Kaldırıldı", "Başlangıç kaydı silindi. Program kapatılıyor. Şimdi klasörü silebilirsiniz.")
            self.root.after(0, self.root.destroy)

    # ---------- SERVİSLER ----------
    def _start_services(self):
        self.behavior.start()
        self.rt.start()
        self.log("✅ NovaGuard başlatıldı.")
        self.log(f"📊 Veritabanı Hazır.")

    def _toggle_game(self):
        State.game_mode = self.game_var.get()
        if State.game_mode:
            self.log("🎮 OYUN MODU AKTİF: Arka plan tarama yavaşlatıldı.")
            self.lbl_status.configure(text="🎮 Oyun Modu", text_color="#ff8c00")
        else:
            self.log("⚡ OYUN MODU KAPALI: Tam koruma aktif.")
            self.lbl_status.configure(text="● Sistem Aktif", text_color="#00ff88")

    def log(self, msg):
        def _a():
            t = time.strftime("%H:%M:%S")
            self.log_box.insert("end", f"[{t}] {msg}\n")
            self.log_box.see("end")
        self.root.after(0, _a)

    def _update_clock(self):
        try:
            self.clock.configure(text=time.strftime("%H:%M:%S"))
        except Exception:
            pass
        self.root.after(1000, self._update_clock)

    def _update_stats(self):
        self.lbl_stats.configure(text=f"Taranan: {self.scan_count} | Tehdit: {self.threat_count}")

    # ---------- TARAMA ----------
    def _ask_scan(self):
        p = filedialog.askdirectory(title="Taranacak klasörü seç")
        if p:
            threading.Thread(target=self._scan_dir, args=(p,), daemon=True).start()

    def _ask_file_scan(self):
        p = filedialog.askopenfilename(title="Taranacak dosyayı seç")
        if p:
            threading.Thread(target=self._process_file, args=(p, False, False), daemon=True).start()

    def _scan_dir(self, root_path):
        if self.is_scanning:
            self.log("⚠️ Zaten tarama devam ediyor.")
            return
        self.is_scanning = True
        self.log(f"🚀 Tarama başladı: {root_path}")

        files = []
        try:
            for r, _, fs in os.walk(root_path):
                if is_ignored(r):
                    continue
                for f in fs:
                    files.append(os.path.join(r, f))
        except Exception as e:
            self.log(f"❌ Dizin hatası: {e}")
            self.is_scanning = False
            return

        total = len(files)
        self.log(f"📁 Toplam {total} dosya bulundu.")

        for i, fp in enumerate(files, 1):
            self._process_file(fp, is_realtime=False, silent=True)
            if i % 20 == 0 or i == total:
                self.progress.set(i / total if total else 0)

        self.progress.set(0)
        self.log(f"✅ Tarama tamam. Tehdit: {self.threat_count}")
        self.is_scanning = False

    def _process_file(self, path, is_realtime, silent=False):
        self.scan_count += 1
        self._update_stats()

        score, reasons = risk_engine.analyze(path)
        if score == 0:
            if not silent:
                self.log(f"✅ Temiz: {os.path.basename(path)}")
            return

        filename = os.path.basename(path)
        reason_str = ", ".join(reasons)

        if score >= 80:
            self.log(f"🦠 KESİN TEHDİT: {filename} (Risk: {score})")
            self.log(f"   Sebep: {reason_str}")
            res = quarantine.quarantine(path, reason_str, score)
            if res["ok"]:
                self.threat_count += 1
                self._update_stats()
                self.log(f"🔒 Karantinaya alındı: {res['qname']}")
                db.add_history(filename, path, reason_str, score, "Karantina")

        elif score >= 40:
            self.log(f"⚠️ ŞÜPHELİ DOSYA: {filename} (Risk: {score})")
            action = show_warning(filename, reason_str, score)
            
            if action == "block":
                res = quarantine.quarantine(path, reason_str, score)
                if res["ok"]:
                    self.threat_count += 1
                    self._update_stats()
                    self.log(f"🔒 Kullanıcı karantinaya aldı: {res['qname']}")
                    db.add_history(filename, path, reason_str, score, "Kullanıcı Karantinası")
            else:
                self.log(f"⚠️ Kullanıcı dosyayı çalıştırmayı seçti: {filename}")
                db.add_history(filename, path, reason_str, score, "İzin Verildi")
        else:
            self.log(f"ℹ️ Düşük Riskli: {filename} (Risk: {score})")
            db.add_history(filename, path, reason_str, score, "Düşük Risk")

    def _on_new_file(self, path):
        self._process_file(path, is_realtime=True)

    def _on_behavior_alert(self, event):
        msg = f"⚠️ Davranış: PID {event['pid']} ({event['name']}) - {event['reason']}"
        self.log(msg)
        db.add_history(event["name"], f"PID {event['pid']}", event["reason"], 50, "Davranış")

    # ---------- VIRUSTOTAL ----------
    def _ask_vt(self):
        p = filedialog.askopenfilename(title="VirusTotal'de taranacak dosya")
        if not p:
            return
        self.log(f"🌐 VirusTotal sorgulanıyor: {os.path.basename(p)}")
        threading.Thread(target=self._do_vt, args=(p,), daemon=True).start()

    def _do_vt(self, path):
        result = check_virustotal(path)
        self.log(result.replace("\n", " | "))

    # ---------- KARANTİNA ----------
    def _load_quarantine_list(self):
        for w in self.quar_list.winfo_children():
            w.destroy()

        items = quarantine.list_all()
        if not items:
            ctk.CTkLabel(self.quar_list, text="(Karantina boş)", text_color="#888899").pack(pady=20)
            return

        for qname, meta in items.items():
            row = ctk.CTkFrame(self.quar_list, fg_color="#1a1a20", corner_radius=8)
            row.pack(fill="x", pady=4, padx=5)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            ctk.CTkLabel(info, text=f"🦠 {meta.get('threat', 'Bilinmeyen')[:60]}", font=("Segoe UI", 12, "bold"), text_color="#ff5555", anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"Eski konum: {meta.get('original_path', '-')}", font=("Consolas", 10), text_color="#888899", anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"Risk: {meta.get('risk', 0)}/100", font=("Segoe UI", 10), text_color="#ffaa00", anchor="w").pack(fill="x")

            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=10)

            ctk.CTkButton(btns, text="♻️", width=40, height=32, fg_color="#238636", command=lambda q=qname: self._restore_file(q)).pack(pady=2)
            ctk.CTkButton(btns, text="🗑️", width=40, height=32, fg_color="#7a2020", command=lambda q=qname: self._delete_file(q)).pack(pady=2)

    def _restore_file(self, qname):
        r = quarantine.restore(qname)
        if r["ok"]:
            self.log(f"✅ Geri yüklendi: {r['to']}")
            self._load_quarantine_list()
        else:
            self.log(f"❌ Hata: {r.get('error')}")

    def _delete_file(self, qname):
        r = quarantine.delete_forever(qname)
        if r["ok"]:
            self.log(f"🗑️ Kalıcı silindi: {qname}")
            self._load_quarantine_list()

    # ---------- GEÇMİŞ ----------
    def _load_history(self):
        self.hist_box.delete("1.0", "end")
        rows = db.get_history()
        if not rows:
            self.hist_box.insert("end", "(Geçmiş boş)\n")
            return
        for r in rows:
            self.hist_box.insert("end", f"[{r[0]}] {r[1]}\n  Tehdit: {r[2]} | Risk: {r[3]} | Aksiyon: {r[4]}\n\n")

    # ---------- AYARLAR ----------
    def _save_ignores(self):
        from core.config import IGNORE_PATHS
        paths = self.ignore_box.get("1.0", "end").strip().split("\n")
        IGNORE_PATHS.clear()
        for p in paths:
            p = p.strip()
            if p:
                IGNORE_PATHS.append(p)
        self.log(f"✅ İstisna listesi güncellendi ({len(IGNORE_PATHS)} giriş).")

    def run(self):
        self._load_quarantine_list()
        self._load_history()
        self.root.mainloop()