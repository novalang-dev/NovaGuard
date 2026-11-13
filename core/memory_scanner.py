# -*- coding: utf-8 -*-
"""Katman 2.5: Limitli bellek taraması. Win 8.1'de opsiyonel."""
import ctypes
import ctypes.wintypes as wt
import platform

# Windows sürümü kontrolü
IS_WIN81 = platform.version().startswith("6.3")   # 8.1 = 6.3
IS_WIN10 = platform.version().startswith("10.0")

k32 = ctypes.windll.kernel32
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.OpenProcess.restype = wt.HANDLE
k32.VirtualQueryEx.argtypes = [wt.HANDLE, wt.LPCVOID, ctypes.c_void_p, ctypes.c_size_t]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.ReadProcessMemory.argtypes = [
    wt.HANDLE, wt.LPCVOID, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
]
k32.ReadProcessMemory.restype = wt.BOOL
k32.CloseHandle.argtypes = [wt.HANDLE]


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wt.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
    ]


MEM_PATTERNS = [
    b"mimikatz",
    b"sekurlsa::logonpasswords",
    b"vssadmin delete shadows",
    b"powershell -enc",
]


def scan_process_memory(pid, max_region_mb=20, max_total_mb=50):
    """
    PID'in okunabilir bölgelerini tara.
    Win 8.1'de limitler daha düşük (RAM tasarrufu + API kısıtı).
    """
    if IS_WIN81:
        max_region_mb = 10
        max_total_mb = 30

    hits = []
    try:
        h = k32.OpenProcess(0x0400 | 0x0010, False, pid)
    except Exception:
        return hits
    if not h:
        return hits

    addr = 0
    region_limit = max_region_mb * 1024 * 1024
    total_limit = max_total_mb * 1024 * 1024
    total_read = 0
    mbi = MBI()
    max_addr = 0x7FFFFFFF if IS_WIN81 else 0x7FFFFFFFFFFF
    try:
        while addr < max_addr and total_read < total_limit:
            try:
                r = k32.VirtualQueryEx(
                    h, ctypes.c_void_p(addr),
                    ctypes.byref(mbi), ctypes.sizeof(mbi)
                )
            except Exception:
                break
            if r == 0:
                break
            if mbi.State == 0x1000 and mbi.RegionSize < region_limit \
                    and (mbi.Protect & 0xEE):
                try:
                    buf = ctypes.create_string_buffer(mbi.RegionSize)
                    rd = ctypes.c_size_t(0)
                    if k32.ReadProcessMemory(
                        h, ctypes.c_void_p(mbi.BaseAddress),
                        buf, mbi.RegionSize, ctypes.byref(rd)
                    ):
                        data = buf.raw[:rd.value].lower()
                        total_read += rd.value
                        for p in MEM_PATTERNS:
                            if p in data:
                                hits.append(p.decode("latin1"))
                except Exception:
                    pass  # erişim hatası normal
            addr = (mbi.BaseAddress or 0) + mbi.RegionSize
    except Exception as e:
        print(f"[Mem] PID {pid}: {e}")
    finally:
        try:
            k32.CloseHandle(h)
        except Exception:
            pass
    return hits