# Changelog

## [Unreleased]
### Added
- **ﾄ雪ｻ蟻 ng盻･c ti蘯ｿng Nh蘯ｭt (Business Japanese Dojo) MVP**: 
  - UI Dashboard with 6 training gates (Meeting Listening, Meeting Speaking, Business Mail, Document Reading, Keigo & Nuance, Final Boss).
  - Drill interface with AI router integration.
  - After Action Report UI showing AI feedback and routing metadata.
  - Unlock logic for the Final Boss based on average scores.
  - Seed data with 33 business scenarios meeting Phase 2A gate minimums.

## [2026-02-13]
### Added
- **Phase 13: Smart Dashboard:** Language-specific progress tracking (TOEIC for English, Kanji/JLPT for Japanese).
- **Phase 12: Context-Aware Workspace:** Multi-language UI foundation (Enterprise-grade).
- **LanguageSelector Widget:** Dropdown with flags for instant context switching.
- **Dynamic Sidebar:** Menu items now render based on `menu_config.json` and selected language.
- **UserSettings Persistence:** App remembers selected language across sessions.
- **TOEIC Reading Part 5:** Implementation of practice module with AI content generation support.
- **ReadingPart5Widget:** Interactive widget for incomplete sentence questions with explanation support.
- **ToeicReadingTab:** Dedicated tab for Part 5 practice with topic filtering.

### Changed
- **Project Structure:** Major refactoring. Moved utility scripts to `scripts/` and data files to `data/`.
- **Sidebar Refactoring:** Moved from hardcoded nav items to configuration-driven model.
- **Dashboard Refactoring:** Stat cards are now dynamic and context-sensitive.
- **StatsService:** Enhanced to support language-specific aggregation.

### Fixed
- **Language Context Isolation:** Fixed issue where Vocab/Grammar content was mixed across languages.
- **Japanese Menu:** Added missing "T盻ｫ v盻ｱng" and "Ng盻ｯ phﾃ｡p" tabs to Japanese context.

- **噫 Stability Fixes:**
  - Resolved `NameError: name 'QObject' is not defined` in `vocab_tab.py`.
  - Added missing `QObject` and `Signal` imports to `PySide6.QtCore`.
  - Application now starts correctly even if `run.py` bypasses the main entry point logic.

## [2026-02-08]

### Fixed

- **亮・・Learning Map Stabilization:**
  - **Eliminated Rendering Lag**: Fixed performance bottleneck caused by font fallback warnings (MS Sans Serif) and excessive pulse animations on 180+ nodes.
  - **Restored Click Functionality**: Changed `MapView` drag mode to `NoDrag` to properly register clicks on map nodes.
  - **Language Filtering**: Map now correctly displays only grammar units belonging to the currently selected language.
  - **Layout Optimization**: Improved spiral algorithm parameters for better node distribution and reduced overlap.
  - **Stability**: Resolved critical `IndentationError`, `AttributeError`, `TypeError` in async callbacks, and SQLAlchemy `Detached Instance` errors.
  - **Vocab Enrich Progress Bar**: Fixed threading issue where the progress bar was unresponsive during batch operations. Refactored to use `WorkerSignals` for thread-safe updates.

### Added

- **塘 PDF Vocabulary Import (Gemini Vision):**
  - **Smart Extraction**: Implemented `import_pdf_vocab_gemini.py` using Gemini 3 Vision API to extract vocabulary from scanned/image-based PDFs.
  - **Data Ingestion**: Successfully imported 50 words from "DANH Sﾃ，H T盻ｪ.pdf" and 120 idioms from "120 THﾃNH NG盻ｮ + C盻､M T盻ｪ.pdf" into the `EnVocabItem` database.

### Changed

- **雫 Enhanced Flashcards:**
  - **Rich Content**: Now displays examples (`GrammarExample`), usage notes, and common mistakes directly on the back of the card.
  - **Game-like Unlock**: Added a prominent **"笨・ﾄ静｣ hi盻ブ!"** button that marks a unit as Mastered and immediately unlocks subsequent nodes on the map.
  - **SRS Tooltips**: Added helpful descriptions to Again/Hard/Good/Easy buttons to guide user learning.

## [2026-02-07]

### Added

- **亮・・Learning Map (MVP Complete):**
  - **Gamified Grammar Learning**: Visual map of 189 grammar units across 5 Fantasy-themed regions (A1-C1).
  - **4 Node States**: Locked 白, Available 祷, Learning 当, Mastered 箝・with distinct visual styling.
  - **Interactive Features**: Zoom/pan navigation, bezier path lines, progress rings, glow effects.
  - **GrammarTab Integration**: Toggle button "亮・・B蘯｣n ﾄ黛ｻ・ to switch between List View and Map View.
  - **Node Click 竊・Flashcard**: Clicking a node opens the corresponding grammar flashcard.
  - **New Files**:
    - `frontend/models/learning_progress.py` - MapStatus, MapRegion, LearningProgress model
    - `frontend/services/learning_map_service.py` - CRUD, stats, unlock logic
    - `frontend/ui/widgets/learning_map/` - 5 widget files (map_widget, map_scene, map_view, grammar_node, path_line)

## [2026-02-06]

### Fixed

- **答 English Grammar Library (Major):**
  - **185 Grammar Units Imported**: Successfully extracted and imported grammar lessons from *Essential*, *Intermediate*, and *Advanced Grammar in Use* (Murphy).
  - **Full Level Coverage**: Spanning A1-A2, B1-B2, and C1-C2 CEFR levels.
  - **13 New Categories**: Created dedicated categories with icons for Tenses, Modals, Conditionals, v.v.
  - **Extraction Tooling**: Developed `extract_english_grammar_v2.py` using optimized TOC parsing for robust PDF extraction.
  - **Import Pipeline**: Created `import_english_grammar.py` using unified database services.
- **噫 Stability & UI Fixes:**
  - Resolved `AttributeError: 'ToeicQuestionCard' object has no attribute 'ai_btn'`.
  - Fixed `TypeError: 'coroutine' object is not callable` in `AsyncWorker`.
  - Added missing `ToeicTest` import.
- **投 Data Integrity:**
  - **Zero Vocabulary Count Resolved**: Found and fixed an issue where 9,000+ vocabulary items were unlinked.
  - Linked 7,500+ Japanese items to their respective topics.

## [2026-02-05]

### Added

- Multi-language support foundation for the entire application.
- `VocabItem` unified model in `frontend/models/unified_vocab.py`.
- Migration script `scripts/migrate_v2_unified.py` to consolidate Japanese and English data.
- Search and list support for any language code via `lang` parameter.
- **TOEIC Module (Phase 02 Complete):**
  - Integrated 600+ TOEIC vocabulary words into the unified database.
  - Added batch import scripts (`scripts/import_all_toeic_vocab.py`) for massive data ingestion.
  - Designed full TOEIC learning roadmap (Listening, Reading, SRS).
  - **TOEIC Module (Phase 03 Complete):**
    - Created `ToeicListeningService` and full `ToeicListeningTab` UI.
    - Added interactive `ToeicQuestionCard` for Part 1 (Photos) and Part 2 (Question-Response).
    - Added import scripts for Listening questions (Part 1 & 2 JSON support).

### Changed

- Refactored `VocabService` to handle unified vocabulary operations.
- Migrated 8391 vocabulary items to the new unified schema (8387 JP, 4 EN).
- Unified field names across languages: `term`, `reading`, `meaning`, `meta_data`, `examples`.

## [2026-01-18]

### Added

- **笨ｨ Vocabulary Tinder Mode (Complete):**
  - Fully responsive card interface (Mobile/Desktop friendly).
  - Multi-language AI TTS (Sequential Japanese-Vietnamese reading).
  - "AI Enrich" feature for real-time vocabulary data enhancement.
  - Auto-scrolling content areas for rich descriptions.

### Fixed

- **ｧ SRS Unification (v1.2.0):**
  - **SRSService**: Centralized "brain" using the SM-2 algorithm for standardized memory retention across all tabs.
  - **KanjiService**: Refactored database logic for Kanji into a dedicated service, separating UI from data.
  - **Database Migration**: Added SRS tracking fields (streak, ease factor, intervals) to the Grammar table.
  - **Holistic Integration**: Unified Vocab, Kanji, and Grammar tabs to use the same logic for review scheduling.
- **式 Gamification & UI:**
  - **Kanji Dashboard Wall**: Fixed "B蘯｣n ﾄ黛ｻ・cﾃｴng trﾃｬnh" not updating. Now counts 'Reviewing' items (0.5 points) towards progress.
  - **Auto-Refresh**: Dashboard now automatically updates after study sessions.
  - **Vietnamese TTS**: Added `strip_emojis` to prevent reading icon names (e.g., "bﾃｴng hoa", "bﾃｳng ﾄ妥ｨn") during text-to-speech.
- **噫 Stability:**
  - Fixed `AttributeError: stop` in `TTSService`.
  - Fixed `NameError: QSizePolicy` in `TinderCard`.
  - Resolved `AttributeError` in `GrammarTab` and `KanjiTab` by standardizing view stacks and attribute initialization.
  - Implemented `hasattr` safety checks in asynchronous UI update callbacks.
- **耳 UI/UX:**
  - Standardized sidebar and view-switching logic across all tabs.
  - Refactored Kanji browser to use nested `QStackedWidget` for seamless study mode switching.
  - Resolved button overlapping and collision with Pomodoro Timer.
  - Fixed text wrapping issues in Tinder cards.
