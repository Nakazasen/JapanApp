"""Setup script để tự động cài đặt và khởi tạo project."""
import os
import sys
import subprocess
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_command(cmd, description):
    """Chạy command và hiển thị progress."""
    print(f"\n{'='*60}")
    print(f"{description}...")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Lỗi: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    """Main setup function."""
    print("="*60)
    print("SETUP ỨNG DỤNG HỌC TIẾNG ANH & TIẾNG NHẬT")
    print("="*60)
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 1. Tạo .env từ env_example.txt nếu chưa có
    env_file = project_root / ".env"
    env_example = project_root / "env_example.txt"
    
    if not env_file.exists() and env_example.exists():
        print("\n1. Tạo file .env từ env_example.txt...")
        import shutil
        shutil.copy(env_example, env_file)
        print("✓ Đã tạo file .env")
    elif env_file.exists():
        print("\n1. File .env đã tồn tại, bỏ qua...")
    else:
        print("\n1. Cảnh báo: Không tìm thấy env_example.txt")
    
    # 2. Tạo virtual environment nếu chưa có
    venv_path = project_root / "venv"
    if not venv_path.exists():
        print("\n2. Tạo virtual environment...")
        if not run_command(f"{sys.executable} -m venv venv", "Tạo venv"):
            print("Lỗi khi tạo virtual environment!")
            return
        print("✓ Đã tạo virtual environment")
    else:
        print("\n2. Virtual environment đã tồn tại, bỏ qua...")
    
    # 3. Activate venv và cài đặt dependencies
    print("\n3. Cài đặt dependencies...")
    
    # Xác định pip command dựa trên OS
    if sys.platform == "win32":
        pip_cmd = str(venv_path / "Scripts" / "pip.exe")
        python_cmd = str(venv_path / "Scripts" / "python.exe")
    else:
        pip_cmd = str(venv_path / "bin" / "pip")
        python_cmd = str(venv_path / "bin" / "python")
    
    if not Path(pip_cmd).exists():
        pip_cmd = f"{sys.executable} -m pip"
        python_cmd = sys.executable
    
    if not run_command(f"{pip_cmd} install --upgrade pip", "Nâng cấp pip"):
        print("Cảnh báo: Không thể nâng cấp pip")
    
    # Try to install basic dependencies first
    requirements_file = project_root / "requirements_basic.txt"
    if requirements_file.exists():
    # Try to install basic dependencies
    result = run_command(f"{pip_cmd} install -r requirements_basic.txt", "Cài đặt dependencies cơ bản")
    if not result:
        print("⚠ Cảnh báo: Có lỗi khi cài đặt một số dependencies")
        print("Bạn có thể cài thủ công sau bằng:")
        print(f"  {pip_cmd} install -r requirements_basic.txt")
        response = input("\nTiếp tục với các bước khác? (y/n): ")
        if response.lower() != 'y':
            return
    else:
        print("✓ Đã cài đặt dependencies cơ bản")
        
        # Note about packages requiring Rust
        print("\n" + "="*60)
        print("LƯU Ý: Các package sau cần Rust hoặc pre-built wheels:")
        print("  - llama-cpp-python (cho Phi-3)")
        print("  - faster-whisper (cho Whisper)")
        print("\nBạn có thể cài sau bằng:")
        print("  pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu")
        print("  pip install faster-whisper")
        print("="*60)
    else:
        if not run_command(f"{pip_cmd} install -r requirements.txt", "Cài đặt dependencies"):
            print("Lỗi khi cài đặt dependencies!")
            return
        print("✓ Đã cài đặt dependencies")
    
    # 4. Khởi tạo database
    print("\n4. Khởi tạo database...")
    if not run_command(f"{python_cmd} scripts/init_db.py", "Khởi tạo database"):
        print("Lỗi khi khởi tạo database!")
        return
    print("✓ Đã khởi tạo database")
    
    # 5. Tạo thư mục AI_Models nếu chưa có
    ai_models_path = Path(r"D:\AI_Models")
    if not ai_models_path.exists():
        print("\n5. Tạo thư mục AI_Models...")
        ai_models_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Đã tạo thư mục {ai_models_path}")
    else:
        print("\n5. Thư mục AI_Models đã tồn tại...")
    
    # 6. Hướng dẫn tải models
    print("\n" + "="*60)
    print("SETUP HOÀN TẤT!")
    print("="*60)
    print("\nCác bước tiếp theo:")
    print("1. Tải Phi-3 model từ HuggingFace:")
    print("   - Truy cập: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf")
    print("   - Tải file phi-3-mini-4k-instruct.gguf")
    print(f"   - Lưu vào: {ai_models_path}")
    print("\n2. (Tùy chọn) Cập nhật đường dẫn model trong file .env:")
    print("   PHI3_MODEL_PATH=D:\\AI_Models\\phi-3-mini-4k-instruct.gguf")
    print("\n3. Chạy ứng dụng:")
    print("   - Backend: python scripts/start_backend.py")
    print("   - Frontend: python scripts/start_frontend.py")
    print("   - Hoặc: python scripts/start_all.py (chạy cả hai)")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

