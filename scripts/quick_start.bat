@echo off
REM Quick start script for Windows
echo ============================================================
echo QUICK START - ỨNG DỤNG HỌC TIẾNG ANH & TIẾNG NHẬT
echo ============================================================

cd /d "%~dp0\.."

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment chua duoc tao!
    echo Dang chay setup.py...
    python setup.py
    if errorlevel 1 (
        echo Loi khi setup! Vui long kiem tra lai.
        pause
        exit /b 1
    )
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo File .env chua ton tai!
    if exist "env_example.txt" (
        copy env_example.txt .env
        echo Da tao file .env tu env_example.txt
    )
)

REM Check if database exists
if not exist "db\app.db" (
    echo Database chua duoc khoi tao!
    echo Dang khoi tao database...
    python scripts\init_db.py
    if errorlevel 1 (
        echo Loi khi khoi tao database!
        pause
        exit /b 1
    )
)

REM Start application
echo.
echo ============================================================
echo KHOI DONG UNG DUNG
echo ============================================================
echo.

python scripts\start_all.py

pause

