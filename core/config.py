# -*- coding: utf-8 -*-
import os
import ctypes
import string
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUARANTINE_DIR = os.path.join(BASE_DIR, "quarantine")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "signatures.db")
HISTORY_DB_PATH = os.path.join(DATA_DIR, "history.db")
IGNORE_FILE = os.path.join(DATA_DIR, "ignore.json")
VT_API_KEY = "f75cf7813eb8d945568631c0178190356cd867fd8010b6e561922808d7c1f098" 

CHUNK_SIZE = 4096
MAX_HEURISTIC_SIZE = 5 * 1024 * 1024
BEHAVIOR_INTERVAL = 5 

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
        if bitmask & 1: drives.append(f"{letter}:\\")
        bitmask >>= 1
    return drives

for drive in get_all_drives():
    if not os.environ.get("SystemDrive", "C:").startswith(drive[0]):
        WATCH_PATHS.append(drive)

# --- VARSAYILAN İSTİSNALAR ---
IGNORE_PATHS = [
    "C:\\Windows\\",
    "C:\\Program Files\\",
    "C:\\Program Files (x86)\\",
    
]

# --- İSTİSNALARI YÜKLE VE KAYDET ---
def load_ignores():
    global IGNORE_PATHS
    if os.path.exists(IGNORE_FILE):
        try:
            with open(IGNORE_FILE, "r", encoding="utf-8") as f:
                IGNORE_PATHS = json.load(f)
        except: pass

def save_ignores(paths):
    global IGNORE_PATHS
    IGNORE_PATHS = paths
    try:
        with open(IGNORE_FILE, "w", encoding="utf-8") as f:
            json.dump(IGNORE_PATHS, f, ensure_ascii=False, indent=2)
    except: pass

load_ignores() # Program açılırken istisnaları yükle

for d in (DATA_DIR, QUARANTINE_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)