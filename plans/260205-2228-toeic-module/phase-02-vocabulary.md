# Phase 02: TOEIC Vocabulary

**Status:** ✅ Complete
**Dependencies:** Phase 01 (Database)
**Est. Time:** 4 hours
**Actual Time:** ~20 min

---

## Objective

Thêm từ vựng TOEIC vào hệ thống vocabulary đã có:

- 600+ từ vựng TOEIC cơ bản
- Phân loại theo chủ đề
- Tích hợp với SRS system có sẵn

---

## Requirements

### Functional

- [ ] Import 600 từ vựng TOEIC vào `VocabItem` (lang="en", source="TOEIC")
- [ ] Phân loại theo 10 chủ đề chính
- [ ] Hiển thị trong Vocab Tab với filter "TOEIC"
- [ ] SRS hoạt động bình thường

### TOEIC Vocabulary Topics

| Topic | Số từ ước tính |
|-------|----------------|
| Office & Business | 80 |
| Finance & Banking | 60 |
| Human Resources | 50 |
| Travel & Tourism | 60 |
| Dining & Restaurants | 40 |
| Shopping & Retail | 50 |
| Health & Medical | 40 |
| Technology | 60 |
| Manufacturing | 50 |
| General | 110 |

---

## Implementation Steps

1. [ ] Tạo file Excel/JSON với 600 từ TOEIC
2. [ ] Tạo script import `scripts/import_toeic_vocab.py`
3. [ ] Map fields: word → term, definition → meaning, IPA → reading
4. [ ] Set `source_material = "TOEIC"` và `level` theo topic
5. [ ] Thêm examples cho mỗi từ
6. [ ] Run import script
7. [ ] Verify trong Vocab Tab
8. [ ] Test SRS với từ TOEIC

---

## Data Format

```json
{
  "term": "negotiate",
  "reading": "/nɪˈɡoʊʃieɪt/",
  "meaning": "đàm phán, thương lượng",
  "lang": "en",
  "level": "TOEIC",
  "source_material": "TOEIC",
  "meta_data": {
    "topic": "Business",
    "pos": "verb"
  },
  "examples": [
    {
      "sentence": "We need to negotiate the contract terms.",
      "translation": "Chúng ta cần đàm phán các điều khoản hợp đồng."
    }
  ]
}
```

---

## Files to Create/Modify

- `data/toeic/toeic_vocabulary.json` - Word list
- `scripts/import_toeic_vocab.py` - Import script
- `frontend/ui/tabs/vocab_tab.py` - Add TOEIC filter (optional)

---

## Test Criteria

- [ ] 600 từ imported successfully
- [ ] Filter by source="TOEIC" works
- [ ] SRS review includes TOEIC words
- [ ] Flashcard shows word + IPA + meaning

---

**Next Phase:** → Phase 03 (Listening Part 1-2)
