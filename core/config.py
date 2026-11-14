# -*- coding: utf-8 -*-
import os
import ctypes
import string

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUARANTINE_DIR = os.path.join(BASE_DIR, "quarantine")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "signatures.db")
HISTORY_DB_PATH = os.path.join(DATA_DIR, "history.db")
VT_API_KEY = "f75cf7813eb8d945568631c0178190356cd867fd8010b6e561922808d7c1f098" # Sonra dolduracağız

CHUNK_SIZE = 4096
MAX_HEURISTIC_SIZE = 5 * 1024 * 1024
BEHAVIOR_INTERVAL = 5 # Oyun modunda bu süre artacak

# İzlenecek ve taranacak yerler
USER_HOME = os.environ.get("USERPROFILE") or os.path.expanduser("~")
WATCH_PATHS = [
    os.path.join(USER_HOME, "Downloads"),
    os.path.join(USER_HOME, "Desktop"),
    os.path.join(USER_HOME, "Documents"),
]

def get_all_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(f"{letter}:\\")
        bitmask >>= 1
    return drives

for drive in get_all_drives():
    if not os.environ.get("SystemDrive", "C:").startswith(drive[0]):
        WATCH_PATHS.append(drive)

# İstisna (Görmezden gelinecek) klasörler
IGNORE_PATHS = [
    "C:\\Windows\\",
    "C:\\Program Files\\",
    "C:\\Program Files (x86)\\",
    # Buraya oyun klasörlerini ekleyebilirsin:
    # "D:\\SteamLibrary\\", 
]

for d in (DATA_DIR, QUARANTINE_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)