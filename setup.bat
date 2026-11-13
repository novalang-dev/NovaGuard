@echo off
chcp 65001 >nul
echo ============================================
echo   NovaGuard Ortam Kurulumu
echo ============================================

python --version >nul 2>&1
if %errorlevel%==0 (
    python --version | findstr /C:"3.10" /C:"3.11" /C:"3.12" >nul
    if %errorlevel%==0 (
        echo [OK] Uygun Python surumu bulundu.
        goto :install_pkgs
    )
    echo [UYARI] Python 3.15 gibi uyumsuz bir surum var.
    echo        winget ile 3.11 kurulacak.
)

echo [..] Python 3.11 kuruluyor (winget)...
winget install --id Python.Python.3.11 -e --scope user --silent --accept-source-agreements --accept-package-agreements
if not %errorlevel%==0 (
    echo [HATA] winget basarisiz. Python 3.11'i python.org'dan manuel kur.
    pause
    exit /b 1
)

REM Bu oturum icin PATH guncelle (yeni terminal acinca zaten gelir)
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"

:install_pkgs
echo [..] Kutuphaneler kuruluyor...
python -m pip install --upgrade pip
python -m pip install psutil watchdog customtkinter
if not %errorlevel%==0 (
    echo [HATA] Kutuphane kurulumu basarisiz.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Kurulum tamamlandi! Simdi: python run.py
echo ============================================
pause