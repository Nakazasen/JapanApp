# 💡 BRIEF: Nâng tầm Trải nghiệm & Tái cấu trúc UI/UX (Enterprise Grade)

**Ngày tạo:** 2026-02-13
**Yêu cầu từ:** User (Muốn phong cách Enterprise hiện đại, tách bạch ngôn ngữ)

---

## 1. VẤN ĐỀ CẦN GIẢI QUYẾT ("Pain Point")
- **Quá tải thông tin (Cognitive Overload):** Người dùng mới vào app bị "ngộp" bởi quá nhiều Tab (Toeic, Hán tự, Ngữ pháp...) trộn lẫn.
- **Thiếu định hướng (Lack of Focus):** Không biết bắt đầu từ đâu.
- **Khó mở rộng (Scalability):** Nếu sau này thêm Tiếng Trung/Hàn, giao diện sẽ vỡ trận.

## 2. GIẢI PHÁP ĐỀ XUẤT: "Context-Aware Workspace"

Thay vì hiển thị tất cả, App sẽ biến hình dựa trên **Ngữ cảnh (Context)** người dùng chọn.

### 🔑 Key Concept: "One Language, One Workspace"
- Khi chọn **Tiếng Anh**: App chỉ là một ứng dụng học Tiếng Anh chuyên nghiệp.
- Khi chọn **Tiếng Nhật**: App "biến hình" thành không gian đậm chất Nhật Bản.

## 3. THIẾT KẾ UX/UI (Enterprise Standard)

### A. Vị trí "Language Selector" 🌍
- **Vị trí:** Sidebar Header (Góc trên cùng bên trái), nơi dễ thấy nhất.
- **Style:** Dropdown hiện đại, có cờ quốc gia (🇺🇸 / 🇯🇵).
- **Behavior:** Khi đổi ngôn ngữ, toàn bộ Menu bên dưới thay đổi theo hiệu ứng mượt mà (Fade/Slide).

### B. Cấu trúc Menu (Sidebar)
Menu được chia làm 3 phần rõ rệt:

#### 1. 🏢 GLOBAL ZONE (Luôn hiển thị)
Các tính năng dùng chung, không phụ thuộc ngôn ngữ:
- 🏠 **Dashboard** (Tổng quan tiến độ tất cả các môn)
- ⚙️ **Cài đặt** (Giao diện, âm thanh, tài khoản)
- 👤 **Hồ sơ của tôi**

#### 2. 📚 LEARNING ZONE (Thay đổi theo ngôn ngữ)
**Nếu chọn 🇬🇧 Tiếng Anh:**
- 📘 Từ vựng (Flashcard)
- 🎧 Luyện Nghe
- 📖 Ngữ pháp
- 🏆 Luyện thi TOEIC (Dashboard, Reading, Listening)
- 📝 Full Mock Test

**Nếu chọn 🇯🇵 Tiếng Nhật:**
- ⛩️ Hán tự (Kanji)
- 🗾 Bảng chữ cái (Kana)
- 🏯 Ngữ pháp (JLPT)
- 🎏 Luyện thi JLPT
- 🗣️ Luyện Nói (Kaiwa)

#### 3. 🧩 TOOLS & EXTENSIONS (Luôn hiển thị hoặc tuỳ biến)
- 🤖 Trợ lý AI (Content Factory)
- 📰 Tin tức song ngữ
- 📺 YouTube Learning

## 4. CÔNG NGHỆ & KIẾN TRÚC ("Under the Hood")

Để đạt chuẩn Enterprise và dễ scale sau này:

- **State Management:** Dùng một `GlobalStore` để lưu trạng thái `current_language`.
- **Dynamic Routing:** Menu không được fix cứng ("hard-coded"). Nó sẽ render dựa trên file cấu hình (JSON config).
  - Ví dụ: `menu_config.json` sẽ định nghĩa: `language="en" -> show tags [A, B, C]`.
- **Lazy Loading (Tối ưu hiệu năng):** Khi đang học Tiếng Anh, các module Tiếng Nhật sẽ **không được load vào bộ nhớ**. Giúp app nhẹ, khởi động nhanh.

## 5. LỘ TRÌNH THỰC HIỆN MVP

### 🚀 Giai đoạn 1 (Core Framework)
- [ ] Thiết kế lại Sidebar với ComboBox chọn ngôn ngữ.
- [ ] Xây dựng hệ thống `MenuConfig` động.
- [ ] Tách các Tab hiện tại vào đúng nhóm (Anh/Nhật).

### 🎁 Giai đoạn 2 (User Experience)
- [ ] Lưu trạng thái ngôn ngữ vào `preferences.json` (Lần sau mở app tự nhớ).
- [ ] Thêm hiệu ứng chuyển đổi mượt mà.
- [ ] Dashboard tổng hợp hiển thị: "Hôm nay bạn học: 30p Tiếng Anh, 15p Tiếng Nhật".

---
**Kết luận:** Giải pháp này biến App từ một "Nồi lẩu thập cẩm" thành một **"Trung tâm đào tạo đa ngôn ngữ"** chuyên nghiệp.
