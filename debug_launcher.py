import subprocess
import sys
import os

python_exe = r"c:\ProgramData\Sandbox\Projects\EnglishApp\venv\Scripts\python.exe"
run_script = r"c:\ProgramData\Sandbox\Projects\EnglishApp\run.py"

print(f"Launching {run_script} with {python_exe}...")
with open("crash_debug.log", "w", encoding="utf-8") as f:
    try:
        subprocess.run([python_exe, run_script], stdout=f, stderr=f, cwd=os.getcwd())
    except Exception as e:
        f.write(f"\nLauncher Error: {e}")
print("Finished. Check crash_debug.log")
