import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Script đềEtải Whisper model cho faster-whisper."""
import os
import sys
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
    """Download Whisper model."""
    print("="*60)
    print("TẢI WHISPER MODEL")
    print("="*60)
    
    print("\nLưu ý: faster-whisper sẽ tự động tải model khi sử dụng lần đầu.")
    print("Model sẽ được cache tại: ~/.cache/huggingface/whisper/")
    
    print("\nCác model có sẵn:")
    print("  - tiny: ~39 MB (nhanh nhất, đềEchính xác thấp)")
    print("  - base: ~74 MB (cân bằng)")
    print("  - small: ~244 MB (khuyến nghềE")
    print("  - medium: ~769 MB (chất lượng cao)")
    print("  - large: ~1550 MB (chất lượng tốt nhất)")
    
    print("\nĐềEtải model tự động, bạn có thềE")
    print("1. Sử dụng Speaking tab - model sẽ tự động tải khi bạn ghi âm lần đầu")
    print("2. Hoặc chạy script test:")
    print("   python -c \"from faster_whisper import WhisperModel; m = WhisperModel('small')\"")
    
    print("\nNguồn tải:")
    print("  - Repository: openai/whisper (trên HuggingFace)")
    print("  - URL: https://huggingface.co/openai/whisper-base")
    print("  - Model được tải tự động bởi faster-whisper")
    
    print("\n" + "="*60)
    print("Model sẽ được tải tự động khi bạn sử dụng Speaking tab!")
    print("="*60)


if __name__ == "__main__":
    main()


