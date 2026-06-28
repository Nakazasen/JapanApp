# Phase 04: Reading Part 5

**Status:** ⬜ Pending
**Dependencies:** Phase 01 (Database)
**Est. Time:** 4 hours

---

## Objective

Xây dựng Reading Practice cho Part 5 (Incomplete Sentences):

- Hiển thị câu với chỗ trống
- 4 options (A, B, C, D)
- Answer checking + explanation
- Grammar topic tagging

---

## Requirements

### Part 5: Incomplete Sentences

- 30 câu/bộ (giống thật)
- Mỗi câu có 4 options
- Hiển thị đáp án đúng + giải thích
- Filter theo grammar topic

### Grammar Topics

| Topic | Ví dụ |
|-------|-------|
| Verb Tense | present/past/future |
| Subject-Verb Agreement | singular/plural |
| Pronouns | he/him/his |
| Prepositions | in/on/at |
| Conjunctions | and/but/or |
| Word Forms | noun/verb/adj/adv |
| Comparatives | more/most/-er/-est |
| Articles | a/an/the |

---

## UI Layout

```
┌─────────────────────────────────────────┐
│  📖 READING PRACTICE - Part 5           │
├─────────────────────────────────────────┤
│                                         │
│  Question 12/30                         │
│                                         │
│  The manager _______ the report         │
│  before the meeting started.            │
│                                         │
│  ○ (A) review                          │
│  ○ (B) reviews                         │
│  ● (C) reviewed                        │
│  ○ (D) reviewing                       │
│                                         │
│  [Check Answer]                         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ ✅ Correct! (C) reviewed        │    │
│  │                                 │    │
│  │ 💡 Giải thích:                  │    │
│  │ "before ... started" → quá khứ  │    │
│  │ → dùng past simple "reviewed"   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [← Prev]              [Next →]        │
└─────────────────────────────────────────┘
```

---

## Implementation Steps

1. [ ] Tạo `frontend/ui/tabs/toeic_reading_tab.py`
2. [ ] Tạo Part 5 question display widget
3. [ ] Implement answer selection logic
4. [ ] Add explanation display
5. [ ] Add progress tracking
6. [ ] Filter by grammar topic
7. [ ] Test with sample questions
8. [ ] Add to main navigation

---

## Files to Create

- `frontend/ui/tabs/toeic_reading_tab.py` - Main tab
- `frontend/ui/widgets/reading_question.py` - Question widget
- `data/toeic/reading/part5.json` - Question bank

---

## Test Criteria

- [ ] Questions display correctly
- [ ] Radio button selection works
- [ ] Correct/incorrect feedback shows
- [ ] Explanation displays after answer
- [ ] Progress saved to database
- [ ] Filter by topic works

---

**Next Phase:** → Phase 05 (Progress Dashboard)
