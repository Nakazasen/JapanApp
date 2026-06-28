# Phase 11: AI Content Generation

**Status:** ⬜ Pending
**Dependencies:** Phase 01 (Database), Phase 05 (Dashboard)
**Est. Time:** 4 hours

---

## Objective

Build a "Content Factory" to automatically generate TOEIC questions using Gemini AI, reducing manual data entry effort.

- **Part 5 (Reading):** Generate incomplete sentences with options & explanations.
- **Part 2 (Listening):** Generate Q&A scripts and convert to audio using Edge-TTS.

## Requirements

### Functional
- [ ] **Content Generation Service:**
  - [ ] Use `GeminiClient.generate_json` for reliable structured output.
  - [ ] Support Part 2 (Question-Response) generation.
  - [ ] Support Part 5 (Incomplete Sentences) generation.
- [ ] **UI (ContentGeneratorTab):**
  - [ ] Select Part (Part 2, Part 5) and Topic.
  - [ ] Preview generated content.
  - [ ] "Save to Database" button to persist valid questions.
- [ ] **Audio Generation:**
  - [ ] Automatically generate audio for Listening questions upon creation.

### Non-Functional
- [ ] **Reliability:** Handle AI timeouts or invalid JSON gracefully.
- [ ] **Quality Control:** Allow user to edit generated content before saving.

---

## Implementation Steps

1. [ ] **Update `ContentGenerationService`**
   - Refactor to use `gemini_client.generate_json`.
   - Add `generate_listening_part2(topic)`.
   - Add `save_question_to_db(data)`.

2. [ ] **Enhance `ContentGeneratorTab`**
   - Add "Save" button.
   - Add "Edit" mode (QTextEdit is currently ReadOnly, make it editable or add fields).
   - Add Part 2 support.

3. [ ] **Integration**
   - Connect "Save" action to Service.
   - Verify saved questions appear in `ToeicListeningTab` and `ToeicReadingTab`.

---

## Files to Modify

- `frontend/services/content_generator_service.py` - Add logic.
- `frontend/ui/tabs/content_generator_tab.py` - Update UI.

## Test Criteria

- [ ] Click "Generate Part 5" -> Returns valid JSON structure.
- [ ] Click "Save" -> Question appears in SQLite DB (`ToeicQuestion` table).
- [ ] Click "Generate Part 2" -> Returns script + Audio file generated.
- [ ] Audio plays correctly in UI.

---

**Next Phase:** ✅ Project Complete (Assessment & Optimization)
