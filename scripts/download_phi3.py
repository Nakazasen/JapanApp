import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Script đềEtự động tải Phi-3 model từ HuggingFace."""
import os
import sys
from pathlib import Path
import requests
from tqdm import tqdm

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings


def download_file(url: str, destination: Path, description: str = "Downloading"):
    """Download file with progress bar."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Đang tải từ: {url}")
    print(f"Lưu vào: {destination}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, stream=True, headers=headers, allow_redirects=True)
    response.raise_for_status()
    
    # Check if we got HTML instead of binary file
    content_type = response.headers.get('content-type', '')
    if 'text/html' in content_type:
        raise ValueError("Nhận được HTML thay vì file. URL có thềEkhông đúng.")
    
    total_size = int(response.headers.get('content-length', 0))
    
    if total_size == 0:
        print("Cảnh báo: Không thềExác định kích thước file")
    
    with open(destination, 'wb') as f, tqdm(
        desc=description,
        total=total_size if total_size > 0 else None,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                if total_size > 0:
                    bar.update(len(chunk))
                else:
                    bar.update(len(chunk))


def get_huggingface_download_url(repo_id: str, filename: str) -> str:
    """Lấy download URL từ HuggingFace."""
    # HuggingFace CDN URL - sử dụng direct download
    base_url = "https://huggingface.co"
    # Thử với /resolve/main/ trước
    return f"{base_url}/{repo_id}/resolve/main/{filename}?download=true"


def main():
    """Download Phi-3 model."""
    print("="*60)
    print("TẢI PHI-3 MODEL")
    print("="*60)
    
    # Model info
    repo_id = "microsoft/Phi-3-mini-4k-instruct-gguf"
    filename = "Phi-3-mini-4k-instruct-q4_K_M.gguf"  # Quantized version (smaller)
    model_name = "phi-3-mini-4k-instruct-q4_K_M.gguf"
    
    # Destination
    ai_models_path = Path(settings.ai_models_path)
    ai_models_path.mkdir(parents=True, exist_ok=True)
    destination = ai_models_path / model_name
    
    # Check if already exists
    if destination.exists():
        print(f"\nModel đã tồn tại tại: {destination}")
        response = input("Bạn có muốn tải lại không? (y/n): ")
        if response.lower() != 'y':
            print("Đã hủy.")
            return
        destination.unlink()
    
    print(f"\nRepository: {repo_id}")
    print(f"File: {filename}")
    print(f"Kích thước ước tính: ~2.4 GB")
    print(f"\nĐang tải vềE{destination}...")
    
    try:
        # Try using huggingface_hub library to list and download
        try:
            from huggingface_hub import list_repo_files, hf_hub_download
        except ImportError:
            print("Đang cài huggingface_hub...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub", "--quiet"])
            from huggingface_hub import list_repo_files, hf_hub_download
        
        # List available files
        print("\nĐang kiểm tra các file có sẵn trong repository...")
        try:
            files = list_repo_files(repo_id=repo_id, repo_type="model")
            gguf_files = [f for f in files if f.endswith('.gguf')]
            
            if not gguf_files:
                print("Không tìm thấy file .gguf trong repository!")
                print(f"Các file có sẵn: {files[:10]}")
                raise ValueError("Không tìm thấy file GGUF")
            
            print(f"\nTìm thấy {len(gguf_files)} file GGUF:")
            for i, f in enumerate(gguf_files[:10], 1):
                print(f"  {i}. {f}")
            
            # Try to find q4_K_M version first, then any quantized version
            target_file = None
            for f in gguf_files:
                if 'q4_K_M' in f or 'q4' in f:
                    target_file = f
                    break
            
            if not target_file:
                target_file = gguf_files[0]  # Use first available
            
            print(f"\nĐang tải file: {target_file}")
            
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=target_file,
                cache_dir=str(ai_models_path),
                local_dir=str(ai_models_path)
            )
            
            # Copy to destination if different name
            if Path(downloaded_path).name != model_name:
                import shutil
                final_path = ai_models_path / model_name
                shutil.copy2(downloaded_path, final_path)
                print(f"\n[OK] Đã tải và đổi tên thành: {final_path}")
                destination = final_path
            else:
                print(f"\n[OK] Đã tải thành công: {downloaded_path}")
                destination = Path(downloaded_path)
            
        except Exception as e:
            print(f"\nLỗi khi list files: {e}")
            raise
        
        print("\n" + "="*60)
        print("TẢI HOÀN TẤT!")
        print("="*60)
        print(f"\nModel đã được lưu tại: {destination}")
        print("\nCập nhật file .env:")
        print(f"PHI3_MODEL_PATH={destination}")
        
    except Exception as e:
        print(f"\nLỗi khi tải: {e}")
        print("\nBạn có thềEtải thủ công:")
        print(f"1. Truy cập: https://huggingface.co/{repo_id}")
        print(f"2. Tải file: {filename}")
        print(f"3. Lưu vào: {destination}")
        print(f"\nHoặc các file khác:")
        print("- Phi-3-mini-4k-instruct-f16.gguf (full precision)")
        print("- Phi-3-mini-4k-instruct-q4_K_M.gguf (quantized, recommended)")
        print("- Phi-3-mini-4k-instruct-q8_0.gguf (higher quality quantized)")
    
    # Keep terminal open on Windows
    if sys.platform == "win32":
        print("\n" + "="*60)
        input("Nhấn Enter đềEđóng cửa sềEnày...")


if __name__ == "__main__":
    main()


