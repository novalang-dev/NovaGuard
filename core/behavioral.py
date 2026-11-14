# -*- coding: utf-8 -*-
"""Katman 3: psutil ile süreç izleme + bellek taraması tetikleme."""
import threading
import psutil
from core.config import BEHAVIOR_INTERVAL
from core.realtime import State

SUSPICIOUS_CMDLINE = [
    "powershell -enc", "powershell -encodedcommand",
    "vssadmin delete shadows", "mimikatz", "nc -e ",
    "netcat -e", "-encodedcommand",
    "reg add hkcu\\software\\microsoft\\windows\\currentversion\\run",
]


class BehavioralShield:
    def __init__(self, alert_callback=None):
        self.alert_callback = alert_callback
        self._stop = threading.Event()
        self._thread = None
        self._seen = set()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="NovaGuard-Behavior")
        self._thread.start()
        print("[L3] Davranışsal kalkan başladı.")

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            if not State.game_mode:
                try:
                    self._scan_once()
                except Exception as e:
                    print(f"[L3] döngü: {e}")

            # Oyun modunda bekleme süresini 6 katına çıkar
            wait = BEHAVIOR_INTERVAL * 6 if State.game_mode else BEHAVIOR_INTERVAL
            self._stop.wait(wait)

    def _scan_once(self):
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "cmdline"]):
            try:
                info = proc.info
                pid = info["pid"]
                if pid in self._seen:
                    continue
                cmd = " ".join(info.get("cmdline") or []).lower()
                if not cmd:
                    continue
                for pat in SUSPICIOUS_CMDLINE:
                    if pat in cmd:
                        self._seen.add(pid)
                        event = {
                            "pid": pid,
                            "name": info.get("name"),
                            "cmdline": cmd[:200],
                            "reason": pat,
                            "level": 4,
                            "layer": 3,
                        }
                        if self.alert_callback:
                            try:
                                self.alert_callback(event)
                            except Exception as e:
                                print(f"[L3] cb: {e}")
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception:
                continue