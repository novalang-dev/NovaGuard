# -*- coding: utf-8 -*-
"""Sistem İşlemleri - Başlangıçta çalışma ve kendini koruma."""
import os
import sys
import winreg
import subprocess

def add_to_startup(exe_path):
    """Programı Windows başlangıcına ekler."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NovaGuardUltimate", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Başlangıca eklenemedi: {e}")
        return False

def remove_from_startup():
    """Programı başlangıçtan kaldırır."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "NovaGuardUltimate")
        winreg.CloseKey(key)
    except:
        pass