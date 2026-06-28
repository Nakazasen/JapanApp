# Audit Report - 2026-02-08 (Performance Focus)

## Summary

- 🔴 Critical Issues (Phải sửa ngay): 2
- 🟡 Warnings (Nên sửa): 2
- 🟢 Suggestions (Tùy chọn): 1

Chào anh, em là Khang - Code Auditor. Qua "khám tổng quát" về hiệu năng (thể lực) của App, em thấy app đang có một số "triệu chứng" làm app chạy chậm và đôi khi gây đứng hình. Dưới đây là phác đồ chi tiết:

---

## 🔴 Critical Issues (Phải sửa ngay)

### 1. N+1 Query (Triệu chứng "Vắt kiệt Database")

- **File:** [learning_map_service.py](file:///C:/ProgramData/Sandbox/Projects/EnglishApp/frontend/services/learning_map_service.py#L81-L85)
- **Triệu chứng:** Khi lấy danh sách tiến độ theo vùng (vùng A1, A2...), app tải **TẤT CẢ** cấu trúc ngữ pháp vào RAM rồi mới lọc thủ công (`if get_region_from_level(g.level) == region`).
- **Nguy hiểm:** Khi dữ liệu tăng lên (vài ngàn cấu trúc), trang Map sẽ load cực chậm và tốn RAM vô ích.
- **Phác đồ điều trị:** Dùng `JOIN` ngay trong SQL query để database chỉ trả về đúng những gì cần thiết.

### 2. UI Thread Blocking (Triệu chứng "Đứng hình tạm thời")

- **File:** [tts.py](file:///C:/ProgramData/Sandbox/Projects/EnglishApp/frontend/services/tts.py#L181-L187)
- **Triệu chứng:** Hàm `play_audio` dùng vòng lặp `while` kết hợp `time.sleep(0.1)` để chờ âm thanh phát xong.
- **Nguy hiểm:** Nếu hàm này chạy trên main thread, UI sẽ bị "đứng" (không thể click, không thể cuộn) cho đến khi âm thanh dừng.
- **Phác đồ điều trị:** Chuyển sang mô hình hướng sự kiện (Event-driven) dùng signals hoặc `QTimer` để theo dõi trạng thái phát nhạc thay vì bắt CPU ngồi chờ.

---

## 🟡 Warnings (Nên sửa)

### 1. Thiếu Pagination (Triệu chứng "Ăn quá nhiều cùng lúc")

- **Files:** Hơn 50 vị trí trong `frontend/services/` dùng `.all()` (ví dụ [vocab_service.py](file:///C:/ProgramData/Sandbox/Projects/EnglishApp/frontend/services/vocab_service.py))
- **Nguy hiểm:** Với danh sách từ vựng khổng lồ, việc fetch toàn bộ object sẽ làm giao diện bị khựng khi chuyển tab.
- **Phác đồ điều trị:** Áp dụng `limit` và `offset` (Phân trang) cho các danh sách dài.

### 2. Redundant Query (Triệu chứng "Làm việc thừa")

- **File:** [learning_map_service.py](file:///C:/ProgramData/Sandbox/Projects/EnglishApp/frontend/services/learning_map_service.py#L297-L298)
- **Triệu chứng:** Đoạn code gọi `session.exec(select(LearningProgress)).all()` hai lần liên tiếp mà không có tác dụng gì ở lần đầu.

---

## 🟢 Suggestions (Tùy chọn)

### 1. Optimize `edge-tts`

- Việc khởi tạo `Communicate` có thể được cache hoặc chạy song song để giảm độ trễ khi click nghe phát âm lần đầu.

---

## Next Steps

Anh xem qua các triệu chứng này nhé. Em đề xuất ưu tiên sửa 2 lỗi **🔴 Critical** trước để App mượt mà ngay lập tức.
