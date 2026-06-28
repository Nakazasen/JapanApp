"""Main entry point for EnglishApp."""
import sys
import os
from pathlib import Path
import subprocess

def main():
    # Setup project paths
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    
    # Add root to python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Detect venv
    venv_path = project_root / "venv"
    use_venv = False
    
    if venv_path.exists():
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            
        # Normalize paths for comparison
        current_exe = sys.executable
        target_exe = str(python_exe)
        if sys.platform == "win32":
            current_exe = current_exe.lower()
            target_exe = target_exe.lower()
            
        if python_exe.exists() and current_exe != target_exe:
            use_venv = True
            
    if use_venv:
        print(f"Restarting in venv: {python_exe}")
        # Run with venv python
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")
        # Fix WebEngine rendering issues
        env["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
        subprocess.run([str(python_exe), "frontend/main.py"], env=env, cwd=str(project_root))
    else:
        # Run directly
        print("Starting EnglishApp...")
        
        # Auto-migration check
        try:
            print("Checking migrations...")
            from scripts.migrate_toeic_transcript import migrate
            migrate()
        except ImportError:
            print("Migration script not found, skipping auto-migration.")
        except Exception as e:
            print(f"Migration warning: {e}")

        try:
            from frontend.main import main as app_main
            app_main()
        except ImportError as e:
            print(f"Error importing frontend: {e}")
            print(f"Current sys.path: {sys.path}")
            sys.exit(1)

if __name__ == "__main__":
    main()
