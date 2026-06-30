# English & Japanese & Multi-language Learning Desktop App

This is a comprehensive desktop application designed to help users master multiple languages (currently specialized in Japanese and English) through AI integration, SRS (Spaced Repetition System), and rich interactive features.

## 🌟 Core Features

- **Multi-language Support (New)**: Unified database architecture for English, Japanese, and any future languages (KR, CN, etc).
- **TOEIC Integration:** AI-guided listening and reading drills with granular difficulty progression.
- **Business Japanese Dojo (Địa ngục tiếng Nhật):** Hardcore roleplay and drill system for real-world Japanese business scenarios, including meeting escalation, nuance, and Keigo.
- **AI Resource Layer**: Uses a provider router instead of a Gemini-only path, so tasks can choose offline/demo, free/low-cost, strong language, judge/consensus, or development/audit models by cost, privacy, quota, and quality.
  - **Địa ngục tiếng Nhật**: Business Japanese training factory with scenario generation, keigo/nuance grading, boss-fight judging, SRS weakness loops, and local-first learning memory.
  - **Luyện viết**: Chấm điểm, sửa lỗi ngữ pháp và gợi ý cách diễn đạt tự nhiên.
  - **Luyện nói**: Phân tích phát âm, độ trôi chảy và ngữ điệu (Multimodal AI when configured).
  - **Tra cứu thông minh**: Giải thích từ vựng, ngữ pháp theo ngữ cảnh.
  - See `docs/AI_RESOURCE_LAYER.md` and `docs/JP_BUSINESS_HELL_AI_STRATEGY.md` for provider routing and model-tier policy.
- **Hệ thống học tập toàn diện**:
  - **Từ vựng**: Flashcards, SRS (Spaced Repetition System).
  - **Ngữ pháp**: Kho dữ liệu ngữ pháp phong phú.
  - **Đọc hiểu**: Hỗ trợ đọc sách (EPUB) và tin tức (Web Scraper).
  - **YouTube**: Học qua video song ngữ.
  - **Luyện thi**: Chế độ thi thử JLPT/TOEIC.

## Yêu cầu hệ thống

- **OS**: Windows 10/11
- **Python**: 3.9+
- **Kết nối Internet**: Cần thiết cho các tính năng AI (Gemini) và Online Dictionary.

## Cài đặt

1. **Clone repository**:

   ```bash
   git clone <repository-url> EnglishApp
   cd EnglishApp
   ```

2. **Tạo môi trường ảo (Virtual Env)**:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Cài đặt thư viện**:

   ```bash
   pip install -r requirements.txt
   ```

 4. **Cấu hình AI Resource Layer / Các Provider**:
   - JapanApp sử dụng AI Resource Layer cho phép cấu hình đa dạng các mô hình.
   - **Tải API Keys từ file cục bộ**: Ứng dụng hỗ trợ nạp key tự động từ file tại `D:\Sandbox\AIOS_habbit\API Key.txt` (hoặc đường dẫn tùy chọn qua biến `JAPANAPP_API_KEY_FILE`). Định dạng label-key xen kẽ, JSON và gán biến `.env` đều được hỗ trợ một cách an toàn.
   - **Chế độ hoạt động AI**: Thiết lập biến môi trường `JAPANAPP_AI_MODE` thành `offline` (chỉ dùng demo offline), `auto` (kết hợp tự động/offline), hoặc `live` (ưu tiên kết nối mạng).
   - **Mô hình cục bộ (Phi-3 / Whisper)**: Xem hướng dẫn chi tiết trong `QUICK_START.md`.

5. **Khởi tạo cơ sở dữ liệu**:

   ```bash
   python scripts/create_tables.py
   ```

## Sử dụng

Chạy ứng dụng bằng lệnh:

```bash
python run.py
```

## Cấu trúc Project

```
EnglishApp/
├── frontend/           # Mã nguồn chính
│   ├── core/           # Database, Config, AI Client
│   ├── models/         # Data Models (SQLModel)
│   ├── services/       # Logic xử lý (Auth, Vocab, Exam, etc.)
│   ├── ui/             # Giao diện (PySide6)
│   └── main.py         # Entry point của UI
├── data/               # Dữ liệu (Config, Assets)
├── db/                 # SQLite Database (app.db)
├── scripts/            # Scripts tiện ích
├── run.py              # File khởi động
└── requirements.txt    # Danh sách thư viện
```

## License

MIT License

### Phase 2B AI provider adapters & local key loading

JapanApp now has live adapter plumbing for Gemini plus the 10-provider pool: Groq, Cerebras, OpenRouter, Mistral, SambaNova, Cloudflare Workers AI, HuggingFace, GitHub Models, AI21, and DeepSeek. Key loading is handled safely via `local_key_loader.py` targeting `D:\Sandbox\AIOS_habbit\API Key.txt` without logging secrets. Automated tests use mocked HTTP; live smoke is opt-in via `RUN_LIVE_PROVIDER_SMOKE=1`.

