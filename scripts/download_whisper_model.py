import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Script đềEtải Whisper model vềEtrước với CPU mode."""
import sys
import os
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings


def main():
    """Download Whisper model with CPU mode."""
    print("="*60)
    print("TẢI WHISPER MODEL VỀ TRƯỚC")
    print("="*60)
    
    # Set HuggingFace cache directory
    hf_cache_dir = Path(settings.ai_models_path) / ".cache" / "huggingface"
    hf_cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_cache_dir.parent)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(hf_cache_dir)
    
    print(f"\nCache directory: {hf_cache_dir}")
    print(f"Model sẽ được lưu tại: {hf_cache_dir / 'whisper'}")
    
    model_name = "small"  # Recommended model
    print(f"\nĐang tải Whisper model: {model_name}")
    print("Sử dụng CPU mode đềEtránh lỗi CUDA...")
    
    try:
        from faster_whisper import WhisperModel
        
        print("\n[INFO] Loading Whisper with CPU mode...")
        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8"
        )
        print(f"\n[OK] Whisper model '{model_name}' đã được tải thành công!")
        print(f"Model được cache tại: {hf_cache_dir / 'whisper'}")
        
        # Test transcribe đềEđảm bảo model hoạt động
        print("\nĐang test model...")
        segments, info = model.transcribe("test.wav", language="en")
        print("[OK] Model hoạt động tốt!")
        
    except FileNotFoundError:
        # File không tồn tại nhưng model đã được load, đó là OK
        print("\n[OK] Model đã được tải (file test không tồn tại nhưng không sao)")
    except ImportError:
        print("\n[ERROR] faster-whisper chưa được cài đặt!")
        print("Cài đặt: pip install faster-whisper")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Lỗi khi tải model: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*60)
    print("HOÀN TẤT!")
    print("="*60)
    print("\nModel đã sẵn sàng đềEsử dụng trong Speaking tab.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


