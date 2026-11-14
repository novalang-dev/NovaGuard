# -*- coding: utf-8 -*-
"""Gerçek Zamanlı İzleme (Watchdog) - İstisna ve Oyun Modu destekli."""
import threading
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.config import WATCH_PATHS, IGNORE_PATHS

# Oyun modu global state
class State:
    game_mode = False


def is_ignored(path):
    """Dosya yolu istisna listesindeyse True döner."""
    try:
        p = path.lower()
        return any(p.startswith(ig.lower()) for ig in IGNORE_PATHS)
    except Exception:
        return False


class _Handler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def _handle(self, path):
        if not path:
            return
        if State.game_mode:
            return  # Oyun modunda realtime tarama yapma
        if is_ignored(path):
            return  # İstisna klasöründe
        if not os.path.isfile(path):
            return
        threading.Thread(target=self.callback, args=(path,), daemon=True).start()

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle(event.dest_path)


class RealtimeProtector:
    def __init__(self, on_new_file):
        self.observer = Observer()
        self._ok = False
        for p in WATCH_PATHS:
            try:
                if os.path.isdir(p):
                    self.observer.schedule(_Handler(on_new_file), p, recursive=True)
                    self._ok = True
            except Exception as e:
                print(f"[RT] {p} izlenemedi: {e}")

    def start(self):
        if not self._ok:
            print("[RT] İzlenecek klasör bulunamadı.")
            return
        try:
            self.observer.start()
            print(f"[RT] Gerçek zamanlı koruma aktif ({len(WATCH_PATHS)} nokta).")
        except Exception as e:
            print(f"[RT] Başlatılamadı: {e}")

    def stop(self):
        try:
            self.observer.stop()
            self.observer.join(timeout=2)
        except Exception:
            pass