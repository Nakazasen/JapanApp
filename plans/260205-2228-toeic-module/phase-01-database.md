# Phase 01: Database Schema

**Status:** ✅ Complete
**Dependencies:** None
**Est. Time:** 2 hours
**Actual Time:** ~15 min

---

## Objective

Thiết kế và tạo database schema cho TOEIC module, bao gồm:

- Questions (Listening & Reading)
- Test Sessions
- User Progress tracking

---

## Database Design

### Table: `toeic_questions`

| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Unique ID |
| part | Integer | TOEIC Part (1-7) |
| question_type | String | photo/qr/conversation/talk/grammar/text/reading |
| question_text | Text | Câu hỏi (nếu có) |
| options | JSON | ["A", "B", "C", "D"] |
| correct_answer | String | A/B/C/D |
| audio_path | String | Path to audio file (Part 1-4) |
| image_path | String | Path to image (Part 1) |
| passage | Text | Đoạn văn (Part 6-7) |
| difficulty | Integer | 1-5 |
| topic | String | Office, Travel, Finance... |
| explanation | Text | Giải thích đáp án |

### Table: `toeic_tests`

| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Unique ID |
| name | String | "ETS 2024 Test 1" |
| test_type | String | full/mini/part |
| total_questions | Integer | 200 for full |
| time_limit | Integer | Minutes (120 for full) |

### Table: `toeic_user_progress`

| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Unique ID |
| user_id | Integer | FK to users |
| question_id | Integer | FK to toeic_questions |
| user_answer | String | A/B/C/D |
| is_correct | Boolean | True/False |
| time_spent | Integer | Seconds |
| answered_at | DateTime | Timestamp |

### Table: `toeic_study_sessions`

| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Unique ID |
| user_id | Integer | FK to users |
| session_type | String | vocabulary/listening/reading/test |
| part | Integer | TOEIC Part (nullable) |
| started_at | DateTime | Start time |
| ended_at | DateTime | End time |
| correct_count | Integer | Số câu đúng |
| total_count | Integer | Tổng số câu |
| estimated_score | Integer | Điểm dự đoán |

---

## Implementation Steps

1. [ ] Tạo file `frontend/models/toeic.py`
2. [ ] Define `ToeicQuestion` model
3. [ ] Define `ToeicTest` model
4. [ ] Define `ToeicUserProgress` model
5. [ ] Define `ToeicStudySession` model
6. [ ] Run migration (create tables)

---

## Files to Create

- `frontend/models/toeic.py` - All TOEIC models

---

## Test Criteria

- [ ] Tables created successfully
- [ ] Can insert sample question
- [ ] Can query by part number
- [ ] FK relationships work

---

**Next Phase:** → Phase 02 (TOEIC Vocabulary)
