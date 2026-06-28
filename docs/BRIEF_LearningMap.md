# 💡 BRIEF: Learning Map (Bản đồ Chinh phục Ngữ pháp)

**Ngày tạo:** 2026-02-07
**Feature Type:** Major New Feature

---

## 1. VẤN ĐỀ CẦN GIẢI QUYẾT

- **189 cấu trúc ngữ pháp** quá nhiều, người học bị overwhelm
- Không biết **bắt đầu từ đâu**, học gì trước
- Khó thấy **tiến độ**, dễ bỏ cuộc
- Học kiểu flashcard đơn thuần → nhàm chán

## 2. GIẢI PHÁP: Learning Map

Biến 189 cấu trúc thành **bản đồ game RPG Fantasy**:

- Mỗi cấu trúc = 1 node trên bản đồ
- Nhóm theo level (A1→C1) = các vùng đất khác nhau
- Học xong = mở khóa node tiếp theo
- Boss Fight = test kiến thức cuối mỗi vùng

## 3. ĐỐI TƯỢNG SỬ DỤNG

| Đối tượng | Đặc điểm | Nhu cầu |
|-----------|----------|---------|
| **Người đi làm** | Ít thời gian, học buổi tối | Học nhanh, thấy tiến độ rõ |
| **Tự học** | Không có giáo viên | Lộ trình rõ ràng, tự đánh giá |

## 4. THIẾT KẾ VISUAL

### Style: Fantasy RPG

- **Vùng A1:** 🏝️ Đảo Khởi Đầu (xanh lá, biển)
- **Vùng A2:** 🌲 Rừng Sơ Cấp (xanh đậm, cây cối)
- **Vùng B1:** 🏔️ Núi Trung Cấp (xám, tuyết)
- **Vùng B2:** 🌋 Núi Lửa Nâng Cao (đỏ, cam)
- **Vùng C1:** 🏰 Lâu Đài Master (vàng, tím)

### Node States

```
✅ Mastered  - Sáng, có ngôi sao
🔵 Learning - Đang nhấp nháy
⬜ Available - Mờ nhưng click được
🔒 Locked   - Khóa, cần hoàn thành node trước
⭐ Boss     - Node lớn hơn, có crown
```

## 5. TÍNH NĂNG

### 🚀 MVP (Phase 1)

- [ ] Hiển thị bản đồ với các vùng Fantasy
- [ ] Node cho mỗi cấu trúc với progress ring
- [ ] Click node → mở study view hiện tại
- [ ] Tracking trạng thái (locked/available/learning/mastered)
- [ ] Path lines nối các node

### 🎁 Phase 2

- [ ] **Sentence Builder** ở mỗi node (kéo thả ghép câu)
- [ ] **Boss Node** với Error Correction challenge
- [ ] **Achievement Badges** khi đạt milestone
- [ ] Animation mở khóa node
- [ ] Daily Quest system
- [ ] XP & Level system

### 💭 Backlog

- [ ] Multiplayer challenge
- [ ] Leaderboard
- [ ] Custom avatar

## 6. ƯỚC TÍNH SƠ BỘ

| Hạng mục | Đánh giá |
|----------|----------|
| **MVP** | 🟡 Trung bình (1-2 tuần) |
| **Phase 2** | 🟡 Trung bình (2-3 tuần) |
| **Rủi ro** | UI phức tạp, cần design kỹ |

## 7. INTEGRATION

- Tích hợp với **GrammarTab** hiện tại
- Sử dụng data từ **grammar database** (189 items)
- Lưu progress vào **user_progress** table

## 8. BƯỚC TIẾP THEO

→ Chạy `/plan` để thiết kế chi tiết:

- Database schema cho progress tracking
- UI Component breakdown
- Task list cho từng phase
