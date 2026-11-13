# -*- coding: utf-8 -*-
"""NovaGuard v0.2 giriş noktası — Win 8.1 uyumlu."""
import sys
import platform

def check_env():
    ver = platform.version()
    py = sys.version_info
    print(f"[INFO] Windows sürümü: {ver}")
    print(f"[INFO] Python sürümü: {py.major}.{py.minor}.{py.micro}")

    if ver.startswith("6.3"):
        print("[INFO] Windows 8.1 algılandı.")
        if py.minor > 10:
            print("[UYARI] Windows 8.1'de Python 3.10.11 önerilir. "
                  "3.11+ çalışmayabilir. https://www.python.org/downloads/release/python-31011/")
    if py.minor < 8:
        print("[HATA] Python 3.8+ gerekli.")
        sys.exit(1)


if __name__ == "__main__":
    check_env()
    from ui.main_window import NovaGuardUI
    NovaGuardUI().run()