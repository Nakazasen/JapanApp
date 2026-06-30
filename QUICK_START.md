# Hướng dẫn Quick Start

## Tự động hóa Setup và Chạy

### Windows

**Cách 1: Sử dụng Quick Start Script (Khuyến nghị)**

```bash
# Chạy script tự động setup và khởi động
scripts\quick_start.bat
```

Script này sẽ tự động:
- Tạo virtual environment nếu chưa có
- Cài đặt dependencies
- Tạo file .env từ env_example.txt
- Khởi tạo database nếu chưa có
- Chạy cả backend và frontend

**Cách 2: Sử dụng Python Scripts**

```bash
# 1. Setup project (chỉ cần chạy 1 lần)
python setup.py

# 2. Chạy ứng dụng
python scripts/start_all.py
```

### Linux/Mac

```bash
# 1. Setup project
python3 setup.py

# 2. Chạy ứng dụng
python3 scripts/start_all.py
```

## Các Scripts Có Sẵn

### Setup Scripts

1. **setup.py** - Tự động setup toàn bộ project
   - Tạo virtual environment
   - Cài đặt dependencies
   - Tạo file .env
   - Khởi tạo database
   - Tạo thư mục AI_Models

2. **scripts/download_phi3.py** - Tự động tải Phi-3 model
   ```bash
   python scripts/download_phi3.py
   ```

### Start Scripts

1. **scripts/start_backend.py** - Chạy backend server
   ```bash
   python scripts/start_backend.py
   ```
   Backend sẽ chạy tại: http://127.0.0.1:8000

2. **scripts/start_frontend.py** - Chạy frontend application
   ```bash
   python scripts/start_frontend.py
   ```

3. **scripts/start_all.py** - Chạy cả backend và frontend
   ```bash
   python scripts/start_all.py
   ```

## Workflow Khuyến Nghị

### Lần đầu tiên:

1. **Setup project:**
   ```bash
   python setup.py
   ```

2. **Tải AI models:**
   ```bash
   python scripts/download_phi3.py
   ```
   
   Hoặc tải thủ công từ: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf

3. **Chạy ứng dụng:**
   ```bash
   python scripts/start_all.py
   ```

### Các lần sau:

Chỉ cần chạy:
```bash
python scripts/start_all.py
```

Hoặc trên Windows:
```bash
scripts\quick_start.bat
```

## Lưu ý

- **Phi-3 Model**: Script `download_phi3.py` sẽ tự động tải model quantized (nhỏ hơn, ~2.4GB). Nếu muốn model chất lượng cao hơn, tải thủ công từ HuggingFace.

- **Whisper Models**: Sẽ tự động tải khi sử dụng lần đầu (không cần tải trước).

- **Database**: Sẽ tự động tạo khi chạy `setup.py` hoặc `init_db.py`.

- **Virtual Environment**: Script sẽ tự động tạo và sử dụng venv nếu có.

## Troubleshooting

### Lỗi "Module not found"

Chạy lại setup:
```bash
python setup.py
```

### Lỗi "Database not found"

Chạy init database:
```bash
python scripts/init_db.py
```

### Lỗi "Model not found"

1. Chạy script tải model:
   ```bash
   python scripts/download_phi3.py
   ```

2. Hoặc cập nhật đường dẫn trong `.env` thành đường dẫn tuyệt đối nơi chứa file tải về (ví dụ):
   ```
   PHI3_MODEL_PATH=C:\path\to\your\models\phi-3-mini-4k-instruct-q4_K_M.gguf
   ```

### AI Resource Layer & API Keys

- JapanApp sử dụng **AI Resource Layer** với tính năng Offline Demo mặc định (không yêu cầu API Key).
- Để cấu hình tự động nạp API Keys từ file cục bộ:
  - Mặc định hệ thống tìm kiếm file key tại `D:\Sandbox\AIOS_habbit\API Key.txt`.
  - Có thể đổi đường dẫn này bằng cách cài đặt biến môi trường:
    ```
    JAPANAPP_API_KEY_FILE=C:\path\to\your\API_Key.txt
    ```
  - Hệ thống tự động phân tích cả các định dạng JSON, gán kiểu `.env` (`KEY=val`), và định dạng dòng xen kẽ (Label -> Key) từ file `API Key.txt` một cách an toàn (không ghi nhận key vào log, kiểm tra trạng thái bằng boolean).
- Để điều khiển luồng định tuyến AI:
  - Cấu hình biến môi trường `JAPANAPP_AI_MODE`:
    - `offline`: Chỉ sử dụng `offline_demo` cục bộ (tiết kiệm chi phí, chạy không cần mạng).
    - `auto` (Mặc định): Tự động thử các provider ngoài nếu có API key, nếu lỗi sẽ tự động chuyển hướng về fallback.
    - `live`: Ưu tiên tuyệt đối các API ngoài (ví dụ Gemini, Groq, DeepSeek), chỉ quay về `offline_demo` khi toàn bộ provider ngoài thất bại.
- Danh sách API key được hỗ trợ: `GEMINI_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`, `SAMBANOVA_API_KEY`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `HUGGINGFACE_API_KEY`, `GITHUB_TOKEN`, `AI21_API_KEY`, `DEEPSEEK_API_KEY`.
- Các thiết lập nâng cao khác xem trong `data/ai/provider_profiles.yaml`.


