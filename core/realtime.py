# -*- coding: utf-8 -*-
"""Gerçek zamanlı dosya izleme."""
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class _Handler(FileSystemEventHandler):
    def __init__(self, cb):
        self.cb = cb

    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(target=self.cb, args=(event.src_path,),
                             daemon=True).start()

    def on_moved(self, event):
        if not event.is_directory:
            threading.Thread(target=self.cb, args=(event.dest_path,),
                             daemon=True).start()


class RealtimeProtector:
    def __init__(self, paths, on_new_file):
        self.observer = Observer()
        self._ok = False
        for p in paths:
            try:
                import os
                if os.path.isdir(p):
                    self.observer.schedule(_Handler(on_new_file), p, recursive=True)
                    self._ok = True
            except Exception as e:
                print(f"[RT] {p}: {e}")

    def start(self):
        if not self._ok:
            print("[RT] izlenecek klasör yok.")
            return
        self.observer.start()
        print("[RT] Gerçek zamanlı koruma aktif.")

    def stop(self):
        try:
            self.observer.stop()
            self.observer.join(timeout=2)
        except Exception:
            pass