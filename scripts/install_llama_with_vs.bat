@echo off
REM Script to install llama-cpp-python with Visual Studio environment loaded
setlocal

echo ============================================================
echo CAI DAT LLAMA-CPP-PYTHON VOI VISUAL STUDIO ENVIRONMENT
echo ============================================================

REM Load Visual Studio environment
call "D:\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvars64.bat"

REM Set CMake environment variables
set FORCE_CMAKE=1
set CMAKE_ARGS=-DGGML_CUDA=OFF

REM Change to project directory
cd /d "%~dp0\.."

REM Install llama-cpp-python
echo.
echo Dang cai dat llama-cpp-python...
echo (Qua trinh nay co the mat 10-30 phut, vui long doi...)
echo.

venv\Scripts\python.exe -m pip install llama-cpp-python --no-cache-dir

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo [OK] DA CAI DAT THANH CONG!
    echo ============================================================
    echo.
    echo Ban co the su dung Writing tab voi Phi-3 roi!
) else (
    echo.
    echo ============================================================
    echo [ERROR] Co loi xay ra khi cai dat
    echo ============================================================
)

pause

