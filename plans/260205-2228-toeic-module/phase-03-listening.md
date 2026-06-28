# Phase 03: TOEIC Listening Part 1-2

**Status:** 🟡 In Progress
**Dependencies:** Phase 02 (Vocabulary) ✅
**Estimated Time:** 6 hours

---

## Objective

Xây dựng module luyện nghe TOEIC Part 1 (Photos) và Part 2 (Question-Response), tận dụng hạ tầng Listening có sẵn.

---

## Scope

### TOEIC Listening Structure

| Part | Format | Questions/Set | Focus |
|------|--------|---------------|-------|
| **Part 1** | 1 Photo + 4 Audio Options | 6 | Describe what you see |
| **Part 2** | 1 Question Audio + 3 Response Options | 25 | Question-Response |

### MVP Features

- [ ] Audio player với Play/Pause/Repeat
- [ ] Question UI với 4 choices (A/B/C/D)
- [ ] Answer checking với explanation
- [ ] Progress tracking per question

---

## Requirements

### Functional

- [ ] FR-01: Load TOEIC Listening questions từ database/JSON
- [ ] FR-02: Play audio cho từng câu hỏi
- [ ] FR-03: Hiển thị 4 lựa chọn (A/B/C/D)
- [ ] FR-04: Check đáp án và hiển thị giải thích
- [ ] FR-05: Track progress (đã làm/đúng/sai)
- [ ] FR-06: Repeat audio (slow speed optional)

### Non-Functional

- [ ] NFR-01: Audio load time < 2s
- [ ] NFR-02: UI responsive (không lag khi chuyển câu)
- [ ] NFR-03: Support offline mode (audio cached)

---

## Implementation Steps

### 1. Data Layer

- [ ] **1.1** Create `TOEICQuestion` model (or reuse `ListeningQuestion`)
- [ ] **1.2** Create sample JSON data for Part 1 (10 questions)
- [ ] **1.3** Create sample JSON data for Part 2 (25 questions)
- [ ] **1.4** Create import script for TOEIC listening data

### 2. Service Layer

- [ ] **2.1** Create `TOEICListeningService` or extend `ListeningPracticeService`
- [ ] **2.2** Implement `list_parts()` → Get Part 1, Part 2, etc.
- [ ] **2.3** Implement `list_questions(part_id)` → Get questions for a part
- [ ] **2.4** Implement `check_answer(question_id, selected)`
- [ ] **2.5** Implement `save_progress(question_id, correct)`

### 3. UI Layer

- [ ] **3.1** Create `TOEICListeningTab` widget (new tab)
- [ ] **3.2** Create `TOEICQuestionCard` widget (reusable question display)
- [ ] **3.3** Implement Part selector (Part 1 / Part 2)
- [ ] **3.4** Implement audio player controls (QMediaPlayer)
- [ ] **3.5** Implement answer selection + feedback

### 4. Integration

- [ ] **4.1** Register `TOEICListeningTab` in main navigation
- [ ] **4.2** Connect with existing stats system
- [ ] **4.3** Test offline audio playback

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `frontend/models/toeic_listening.py` | DB models for TOEIC questions |
| `frontend/services/toeic_listening_service.py` | Service for TOEIC listening |
| `frontend/ui/tabs/toeic_listening_tab.py` | Main tab for TOEIC listening |
| `frontend/ui/widgets/toeic_question_card.py` | Reusable question widget |
| `data/toeic/listening_part1.json` | Sample Part 1 data |
| `data/toeic/listening_part2.json` | Sample Part 2 data |

### Modify

| File | Changes |
|------|---------|
| `frontend/core/database.py` | Import new TOEIC models |
| `frontend/main_window.py` | Add TOEIC tab to navigation |

---

## Data Format

### Part 1 Question JSON

```json
{
  "id": 1,
  "part": 1,
  "image_path": "data/toeic/images/part1_001.jpg",
  "audio_path": "data/toeic/audio/part1_001.mp3",
  "options": ["A", "B", "C", "D"],
  "correct_option": "B",
  "transcript": {
    "A": "The man is reading a book.",
    "B": "The man is typing on a computer.",
    "C": "The man is talking on the phone.",
    "D": "The man is writing a letter."
  },
  "explanation": "The image shows a man typing on a computer at his desk."
}
```

### Part 2 Question JSON

```json
{
  "id": 1,
  "part": 2,
  "audio_question_path": "data/toeic/audio/part2_q001.mp3",
  "audio_options_path": "data/toeic/audio/part2_o001.mp3",
  "options": ["A", "B", "C"],
  "correct_option": "A",
  "transcript": {
    "question": "Where is the meeting room?",
    "A": "It's on the second floor.",
    "B": "Yes, at 3 o'clock.",
    "C": "About 20 people."
  },
  "explanation": "This is a 'where' question asking about location. Option A provides a location."
}
```

---

## Test Criteria

- [ ] TC-01: Can load Part 1 questions from JSON
- [ ] TC-02: Audio plays correctly on button click
- [ ] TC-03: Answer selection shows correct/incorrect feedback
- [ ] TC-04: Progress is saved after answering
- [ ] TC-05: Can navigate between questions
- [ ] TC-06: Part 2 questions work similarly

---

## Dependencies

### External

- `QMediaPlayer` (PySide6) - Already available
- Audio files (.mp3) - Need to create/source

### Internal

- Existing `ListeningPracticeTab` patterns
- Existing `ThemeColors` and styling
- Existing database infrastructure

---

## Notes

1. **Audio Sourcing**: Có thể dùng TTS để tạo sample audio ban đầu (Edge-TTS).
2. **Reuse Patterns**: Copy patterns từ `ListeningPracticeTab` (QuestionBlock, audio controls).
3. **Phase 2 Expansion**: Part 3-4 (Conversations & Talks) sẽ tương tự nhưng audio dài hơn.

---

**Next Phase:** [Phase 04: Reading Part 5](phase-04-reading.md)
