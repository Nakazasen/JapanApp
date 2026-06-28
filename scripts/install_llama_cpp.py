import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Script đềEcài đặt llama-cpp-python với hướng dẫn cài Visual Studio Build Tools."""
import sys
import subprocess
import os
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_compiler():
    """Kiểm tra xem có C++ compiler không."""
    try:
        result = subprocess.run(["where", "cl"], capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip() != ""
    except:
        return False

def install_vs_build_tools_guide():
    """Hướng dẫn cài Visual Studio Build Tools."""
    print("="*60)
    print("HƯỚNG DẪN CÀI ĐẶT VISUAL STUDIO BUILD TOOLS")
    print("="*60)
    print("\nllama-cpp-python cần C++ compiler đềEbuild.")
    print("\nCách 1: Cài Visual Studio Build Tools (Khuyến nghềE")
    print("1. Tải Visual Studio Build Tools từ:")
    print("   https://visualstudio.microsoft.com/downloads/")
    print("   (Chọn 'Build Tools for Visual Studio 2022')")
    print("\n2. Trong quá trình cài đặt, chọn:")
    print("   - Desktop development with C++")
    print("   - Windows 10 SDK hoặc Windows 11 SDK")
    print("   - C++ CMake tools")
    print("\n3. Sau khi cài xong, mềEPowerShell mới và chạy:")
    print("   python scripts\\install_llama_cpp.py")
    print("\n" + "="*60)
    
    # Tự động mềEtrình duyệt
    try:
        import webbrowser
        print("\nĐang mềEtrang download Visual Studio Build Tools...")
        webbrowser.open("https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022")
    except:
        pass

def try_install_llama_cpp():
    """Thử cài llama-cpp-python."""
    print("\n" + "="*60)
    print("ĐANG THỬ CÀI ĐẶT LLAMA-CPP-PYTHON")
    print("="*60)
    
    venv_python = Path(__file__).parent.parent / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = sys.executable
    
    # Set environment variables
    env = os.environ.copy()
    env["FORCE_CMAKE"] = "1"
    env["CMAKE_ARGS"] = "-DGGML_CUDA=OFF"
    
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "llama-cpp-python", "--no-cache-dir"],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n[OK] Đã cài đặt llama-cpp-python thành công!")
            return True
        else:
            print("\n[ERROR] Không thềEcài đặt:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"\n[ERROR] Lỗi: {e}")
        return False

def main():
    """Main function."""
    print("="*60)
    print("CÀI ĐẶT LLAMA-CPP-PYTHON")
    print("="*60)
    
    # Kiểm tra compiler
    if check_compiler():
        print("\n[OK] Đã phát hiện C++ compiler!")
        if try_install_llama_cpp():
            print("\nHoàn tất! Bạn có thềEsử dụng Writing tab với Phi-3.")
            return
    else:
        print("\n[WARNING] Không tìm thấy C++ compiler (cl.exe)")
    
    # Hướng dẫn cài Visual Studio Build Tools
    install_vs_build_tools_guide()
    
    print("\n" + "="*60)
    print("LƯU ÁE)
    print("="*60)
    print("\nỨng dụng vẫn có thềEchạy được mà không cần llama-cpp-python.")
    print("ChềEWriting tab (sử dụng Phi-3) sẽ không hoạt động.")
    print("\nCác tab khác vẫn hoạt động bình thường:")
    print("- Vocab, Speaking, YouTube, News, Grammar, Exam, Settings")

if __name__ == "__main__":
    main()


