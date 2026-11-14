# -*- coding: utf-8 -*-
"""NovaGuard Ultimate giriş noktası - Otomatik Kurulum ve Sağ Tık."""
import sys
import os
import threading
import time
import ctypes
import shutil
import winreg
import pystray
from PIL import Image, ImageDraw

# --- 1. SAĞ TIK İÇİN ÖZEL MOD (VirusTotal) ---
if len(sys.argv) > 2 and sys.argv[1] == "--scan-vt":
    file_path = sys.argv[2]
    from core.vt_api import check_virustotal
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("NovaGuard VirusTotal",
                        f"Dosya: {file_path.split(chr(92))[-1]}\n\n{check_virustotal(file_path)}")
    sys.exit(0)

# --- 2. OTOMATİK KURULUM VE KOPYALAMA ---
TARGET_DIR = r"C:\NovaGuard"
TARGET_EXE = os.path.join(TARGET_DIR, "NovaGuard.exe")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def setup_and_relocate():
    if getattr(sys, 'frozen', False):
        current_exe = sys.executable
    else:
        return

    if os.path.abspath(current_exe) == os.path.abspath(TARGET_EXE):
        return

    print("[SYS] Otomatik kurulum başlatılıyor...")
    
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", current_exe, None, None, 1
        )
        sys.exit(0)

    try:
        os.makedirs(TARGET_DIR, exist_ok=True)
        os.system("taskkill /f /im NovaGuard.exe >nul 2>&1")
        time.sleep(1)
        shutil.copy2(current_exe, TARGET_EXE)
        os.startfile(TARGET_EXE)
        sys.exit(0)
    except Exception as e:
        print(f"Kurulum hatası: {e}")
        sys.exit(1)

def install_context_menu():
    try:
        # Windows yollarını ham string (r) ile yazıyoruz
        key_path = r"*\shell\NovaGuardVirusTotal"
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
        winreg.SetValue(key, "", winreg.REG_SZ, "NovaGuard ile VirusTotal'de Tara")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{TARGET_EXE},0")
        winreg.CloseKey(key)

        cmd_path = r"*\shell\NovaGuardVirusTotal\command"
        cmd_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, cmd_path)
        winreg.SetValue(cmd_key, "", winreg.REG_SZ, f'"{TARGET_EXE}" --scan-vt "%1"')
        winreg.CloseKey(cmd_key)
        print("[SYS] Sağ tık menüsü eklendi.")
    except Exception as e:
        print(f"Sağ tık menüsü eklenemedi: {e}")

def add_to_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NovaGuardUltimate", 0, winreg.REG_SZ, f'"{TARGET_EXE}"')
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Başlangıca eklenemedi: {e}")

# --- 3. NORMAL ÇALIŞMA MODU ---
from ui.main_window import NovaGuardUI

_lock_file = None

def create_icon_image():
    img = Image.new("RGB", (64, 64), color="#0a0a0c")
    d = ImageDraw.Draw(img)
    d.polygon([(32, 4), (56, 16), (56, 44), (32, 60), (8, 44), (8, 16)], fill="#00d2ff")
    d.rectangle([28, 20, 36, 44], fill="#0a0a0c")
    d.rectangle([22, 20, 42, 26], fill="#0a0a0c")
    return img

def protect_self():
    global _lock_file
    if getattr(sys, 'frozen', False):
        try:
            _lock_file = open(sys.executable, "rb")
            print("[SYS] Kendini koruma kalkanı aktif.")
        except:
            pass

def main():
    setup_and_relocate()
    install_context_menu()
    add_to_startup()
    protect_self()

    ui = NovaGuardUI()

    def show_window(icon, item):
        ui.root.deiconify()
        ui.root.lift()

    def quit_app(icon, item):
        icon.stop()
        ui.root.after(0, ui.root.destroy)

    icon = pystray.Icon(
        "NovaGuard",
        create_icon_image(),
        "NovaGuard Ultimate - Koruma Aktif",
        menu=pystray.Menu(
            pystray.MenuItem("Arayüzü Aç", show_window, default=True),
            pystray.MenuItem("Çıkış", quit_app),
        ),
    )
    ui.tray_icon = icon

    threading.Thread(target=icon.run, daemon=True).start()
    ui.run()

if __name__ == "__main__":
    main()