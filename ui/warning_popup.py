# -*- coding: utf-8 -*-
"""Tehlikeli dosya uyarı penceresi (Windows Defender tarzı)."""
import customtkinter as ctk


def show_warning(filename, reason, score):
    """
    Tehlikeli dosya açılmaya çalışıldığında çağır.
    'allow' veya 'block' döner.
    """
    result = {"action": "block"}

    win = ctk.CTkToplevel()
    win.title("NovaGuard - Tehdit Engellendi")
    win.geometry("550x480") # Pencere boyutunu büyüttük
    win.attributes("-topmost", True)
    win.configure(fg_color="#0a0a0c")
    win.grab_set()

    # Kırmızı kalkan ikonu
    ctk.CTkLabel(win, text="🛡️", font=("Segoe UI", 64),
                 text_color="#ff4444").pack(pady=(15, 5))

    ctk.CTkLabel(win, text="NovaGuard bir tehdit engelledi!",
                 font=("Segoe UI", 18, "bold"),
                 text_color="#ff4444").pack(pady=5)

    ctk.CTkLabel(win, text=f"Risk Skoru: {score}/100",
                 font=("Segoe UI", 14, "bold"),
                 text_color="#ffaa00").pack(pady=2)

    # Bilgi kutusu
    info_frame = ctk.CTkFrame(win, fg_color="#1a1a20", corner_radius=10)
    info_frame.pack(fill="x", padx=30, pady=10)

    ctk.CTkLabel(info_frame, text="Dosya:", font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(fill="x", padx=15, pady=(10, 0))
    ctk.CTkLabel(info_frame, text=filename, font=("Consolas", 11),
                 text_color="#00d2ff", anchor="w",
                 wraplength=430).pack(fill="x", padx=15, pady=(0, 8))

    ctk.CTkLabel(info_frame, text="Sebep:", font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(fill="x", padx=15, pady=(0, 0))
    ctk.CTkLabel(info_frame, text=reason, font=("Segoe UI", 11),
                 text_color="#ffaa00", anchor="w",
                 wraplength=430).pack(fill="x", padx=15, pady=(0, 10))

    ctk.CTkLabel(win, text="Bu dosya zararlı olabilir. Yine de çalıştırmak istiyor musunuz?",
                 font=("Segoe UI", 11),
                 text_color="#888899").pack(pady=5)

    # Butonlar
    btn_frame = ctk.CTkFrame(win, fg_color="transparent")
    btn_frame.pack(pady=15, fill="x")

    def do_block():
        result["action"] = "block"
        win.destroy()

    def do_allow():
        result["action"] = "allow"
        win.destroy()

    # Butonları yan yana ortalayarak koyuyoruz
    ctk.CTkButton(btn_frame, text="🛡️ Karantinaya Al (Güvenli)",
                  fg_color="#238636", hover_color="#2ea043",
                  width=220, height=40,
                  command=do_block).pack(side="left", padx=(40, 10))

    ctk.CTkButton(btn_frame, text="⚠️ Yine de Çalıştır",
                  fg_color="#3a1515", hover_color="#5a2020",
                  text_color="#ff5555",
                  width=180, height=40,
                  command=do_allow).pack(side="right", padx=(10, 40))

    win.wait_window()
    return result["action"]