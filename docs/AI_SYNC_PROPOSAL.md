# Proposal: AI Settings Sync & Enhancement

Dựa trên yêu cầu đồng bộ từ project `leetcode_mastery`, em đề xuất kế hoạch nâng cấp hệ thống quản lý AI cho `EnglishApp`.

## 🎯 Mục tiêu

- **Exact Parity:** Giao diện và tính năng quản lý AI phải giống 100% project gốc.
- **Robustness:** Tăng tính ổn định bằng cơ chế xoay vòng API Key và Waterfall strategy.
- **UX:** Cải thiện thẩm mỹ và tích hợp cài đặt Pomodoro.

## 📱 Tính năng đề xuất

### 1. Giao diện Premium (AI Settings & Playground)

- Giao diện Dark Mode đồng nhất với dự án gốc.
- Quản lý model bằng bảng với các nút điều hướng màu sắc:
  - `▲` (Xanh lá): Đẩy độ ưu tiên lên.
  - `▼` (Xanh dương): Hạ độ ưu tiên.
  - `✕` (Đỏ): Xóa model.
- Khu vực **Playground** để thử nghiệm (test) API Key và Model ngay lập tức với kết quả phản hồi chi tiết (Latency, Response body).

### 2. Lõi xử lý (Smart AI Service)

- **JSON-based Config:** Lưu cấu hình tại `data/config/ai_settings.json`.
- **Key Rotation:** Tự động chuyển API Key khi gặp lỗi 429 (Too Many Requests).
- **Waterfall strategy:** Tự động thử danh sách model theo thứ tự ưu tiên nếu model trước đó thất bại.

### 3. Tích hợp mở rộng

- Gộp cài đặt **Pomodoro Timer** vào cùng tab AI để quản lý tập trung.

## 🛠️ Công nghệ sử dụng

- **PySide6:** Giao diện người dùng.
- **google-generativeai:** SDK kết nối Gemini.
- **Python json/os/dotenv:** Quản lý cấu hình và môi trường.

---

👉 **Anh muốn:**

1. **Duyệt luôn!** - Chuyển sang tạo danh sách Feature & Phase chi tiết.
2. **Điều chỉnh** - Anh muốn thêm/bớt tính năng nào?
