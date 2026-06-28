import json
import os
import requests
import time
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

def download_file(url, path):
    """Tải một file từ URL và lưu vào đường dẫn chỉ định."""
    if os.path.exists(path):
        return False # Đã có rồi thì bỏ qua
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        # Không in lỗi 404 vì một số tổ hợp có thể không tồn tại, tránh làm rác terminal
        return False

def process_kana_file(filename, type_name):
    print(f"\n--- Đang chuẩn bị dữ liệu OFFLINE cho {type_name} ---")
    content_path = os.path.join('frontend', 'data', 'content', 'intro', filename)
    asset_dir = os.path.join('frontend', 'data', 'assets', 'kana', type_name.lower())
    os.makedirs(asset_dir, exist_ok=True)

    if not os.path.exists(content_path):
        print(f"Lỗi: Không tìm thấy {content_path}")
        return

    with open(content_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Danh sách các chữ cái cần tải
    chars_to_download = set()
    
    # 1. Thu thập từ file JSON (bao gồm cả xé lẻ chữ ghép)
    for section in ['seion', 'dakuon', 'yoon']:
        for item in data.get(section, []):
            char_str = item.get('char', '')
            for char in char_str:
                if char.strip():
                    chars_to_download.add(char)
                    
    # 2. Bổ sung các chữ nhỏ đặc biệt (nhỡ trong JSON không có)
    if type_name == 'Hiragana':
        chars_to_download.update(['ゃ', 'ゅ', 'ょ', 'っ'])
    else:
        chars_to_download.update(['ャ', 'ュ', 'ョ', 'ッ'])

    tasks = []
    base_type = type_name.lower()
    for char in chars_to_download:
        url = f'https://raw.githubusercontent.com/jcsirot/kanji.gif/master/{base_type}/gif/150x150/{quote(char)}.gif'
        dest = os.path.join(asset_dir, f"{char}.gif")
        tasks.append((url, dest, char))

    print(f"Tìm thấy {len(tasks)} thành phần chữ lẻ cần kiểm tra/tải về...")
    
    count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda x: download_file(x[0], x[1]), tasks))
        count = sum(1 for r in results if r)

    print(f"Hoàn thành bảng {type_name}: Đã tải mới {count} file.")

if __name__ == "__main__":
    start_time = time.time()
    
    # Xử lý cả 2 bảng chữ cái
    process_kana_file('hiragana.json', 'Hiragana')
    process_kana_file('katakana.json', 'Katakana')
    
    print(f"\n✅ THÀNH CÔNG: Toàn bộ linh kiện chữ cái đã được lưu offline!")
    print(f"Thời gian thực hiện: {time.time() - start_time:.2f} giây")
