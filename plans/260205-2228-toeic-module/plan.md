# Plan: TOEIC 720 Learning Module

**Created:** 2026-02-05
**Status:** 🟡 In Progress
**Target:** TOEIC 720 trong 3 tháng

---

## Overview

Xây dựng module TOEIC cho EnglishApp, bao gồm:

- Từ vựng TOEIC với SRS
- Listening Practice (Part 1-4)
- Reading Practice (Part 5-7)
- Progress Dashboard & Analytics

---

## Tech Stack

- **Frontend:** PySide6 (Qt for Python) - có sẵn
- **Backend:** SQLite + SQLModel - có sẵn
- **New:**
  - Audio player cho Listening
  - Chart/Graph cho Dashboard
  - Question bank storage

---

## Phases

| Phase | Name | Status | Tasks | Est. Time |
| :--- | :--- | :--- | :--- | :--- |
| 01 | Database Schema | ✅ Complete | 6 | 2h |
| 02 | TOEIC Vocabulary | ✅ Complete | 8 | 4h |
| 03 | Listening Part 1-2 | ✅ Complete | 14 | 6h |
| 04 | Reading Part 5 | ✅ Complete | [View Plan](phase-04-reading.md) | 4h |
| 05 | Progress Dashboard | ✅ Complete | 6 | 3h |

**Total:** 38 tasks | Est. 19 hours (MVP)

---

## Phase 2+ (Sau MVP)

| Phase | Name | Status | Plan | Priority |
|-------|------|--------|------|----------|
| 06 | Listening Part 3-4 | ✅ Complete | [View Plan](phase-06-listening-advanced.md) | Medium |
| 07 | Reading Part 6-7 | ✅ Complete | [View Plan](phase-07-reading-sets.md) | Medium |
| 08 | Full Test Mode | ✅ Complete | [View Plan](phase-08-full-test.md) | High |
| 09 | AI Weak Point Analysis | ✅ Complete | [View Plan](phase-09-ai-analysis.md) | Low |
| 10 | Optimization & Polish | ✅ Complete | [View Plan](phase-10-optimization.md) | Medium |
| 11 | Content Generation (AI) | ✅ Complete | [View Plan](phase-11-content.md) | High |

---

## Quick Commands

- Start Phase 1: `/code phase-01`
- Check progress: `/next`
- Save context: `/save-brain`

---

## Notes

- Tận dụng unified `VocabItem` model đã có cho TOEIC vocab
- Audio files lưu trong `data/toeic/audio/`
- Question bank lưu trong SQLite hoặc JSON
