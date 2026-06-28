import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Script to download AI models."""
import os
import sys
from pathlib import Path
import requests
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings


def download_file(url: str, destination: Path, description: str = "Downloading"):
    """Download file with progress bar."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destination, 'wb') as f, tqdm(
        desc=description,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))


def download_phi3():
    """Download Phi-3 model."""
    print("Downloading Phi-3 model...")
    print("Sử dụng script download_phi3.py đềEtải tự động:")
    print("  python scripts/download_phi3.py")
    print("\nHoặc tải thủ công từ:")
    print("  https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf")
    print(f"Lưu vào: {settings.ai_models_path}")


def download_whisper():
    """Download Whisper model."""
    print("\nDownloading Whisper model...")
    print("Note: faster-whisper will download models automatically on first use.")
    print("Models will be cached in: ~/.cache/huggingface/")
    print("Recommended model: small")
    print("Available models: tiny, base, small, medium, large")
    
    # faster-whisper downloads models automatically
    # No manual download needed


if __name__ == "__main__":
    print("AI Models Download Script")
    print("=" * 50)
    
    # Ensure AI models directory exists
    Path(settings.ai_models_path).mkdir(parents=True, exist_ok=True)
    
    print(f"AI Models Path: {settings.ai_models_path}")
    print()
    
    # Download models
    download_phi3()
    download_whisper()
    
    print("\n" + "=" * 50)
    print("Download complete!")
    print("\nNext steps:")
    print("1. Download Phi-3 GGUF model manually from HuggingFace")
    print("2. Save it to:", settings.ai_models_path)
    print("3. Update PHI3_MODEL_PATH in .env file")
    print("4. Whisper models will be downloaded automatically on first use")


