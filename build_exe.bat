@echo off
setlocal

where py >nul 2>nul
if %errorlevel% neq 0 (
  echo [ERROR] Python launcher ^(py^) not found. Please install Python 3 first.
  exit /b 1
)

echo [1/3] Installing/Upgrading PyInstaller...
py -m pip install --upgrade pyinstaller
if %errorlevel% neq 0 exit /b 1

echo [2/3] Building EXE...
py -m PyInstaller --noconfirm --clean --windowed --onefile --name TodoDesktop app.py
if %errorlevel% neq 0 exit /b 1

echo [3/3] Done.
echo EXE path: dist\TodoDesktop.exe
echo You can double-click dist\TodoDesktop.exe to run.

endlocal
