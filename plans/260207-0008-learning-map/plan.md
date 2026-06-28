# Plan: Learning Map (Bản đồ Chinh phục Ngữ pháp)

**Created:** 2026-02-07
**Status:** 🟡 Planning
**Brief:** [BRIEF_LearningMap.md](file:///c:/ProgramData/Sandbox/Projects/EnglishApp/docs/BRIEF_LearningMap.md)

---

## Overview

Biến 189 cấu trúc ngữ pháp thành bản đồ game RPG Fantasy với 5 vùng đất (A1→C1). Người học mở khóa node dần, thấy tiến độ rõ ràng, có động lực hoàn thành.

## Tech Stack

- **UI Framework:** PySide6 (existing)
- **Graphics:** QGraphicsView + QGraphicsScene (for map rendering)
- **Data:** SQLModel + existing grammar database
- **Storage:** SQLite (app.db)

## Phases

| Phase | Name | Status | Tasks | Est. Time |
|-------|------|--------|-------|-----------|
| 01 | Data Layer & Progress Model | ✅ Complete | 6 | 2-3h |
| 02 | Map Widget Core | ✅ Complete | 8 | 4-5h |
| 03 | Node Components | ✅ Complete | 7 | 3-4h |
| 04 | Integration & Navigation | ✅ Complete | 5 | 2-3h |
| 05 | Polish & Testing | ✅ Complete | 5 | 2-3h |

**Total:** 31 tasks | ~15-18 hours

---

## Phase Details

### Phase 01: Data Layer & Progress Model

- [ ] Create `LearningProgress` model (user_id, grammar_id, status, mastered_at)
- [ ] Create `MapRegion` enum (A1, A2, B1, B2, C1)
- [ ] Add helper to group grammar items by level/region
- [ ] Create progress service (get/update/calculate stats)
- [ ] Migrate existing grammar data to include region tags
- [ ] Unit tests for progress tracking

### Phase 02: Map Widget Core

- [ ] Create `LearningMapWidget` (QWidget container)
- [ ] Create `MapScene` (QGraphicsScene for map)
- [ ] Create `MapView` (QGraphicsView with zoom/pan)
- [ ] Design region background images (Fantasy theme)
- [ ] Implement region switching (click to zoom)
- [ ] Add minimap overlay for navigation
- [ ] Implement smooth zoom animations
- [ ] Add region labels and decorations

### Phase 03: Node Components

- [ ] Create `GrammarNode` (QGraphicsItem)
- [ ] Implement node states (locked/available/learning/mastered)
- [ ] Add progress ring around nodes
- [ ] Create path lines connecting nodes
- [ ] Implement node click → open study view
- [ ] Add hover tooltips with grammar preview
- [ ] Create Boss Node variant (larger, special style)

### Phase 04: Integration & Navigation

- [ ] Add "Map View" toggle to GrammarTab
- [ ] Connect map selection to existing flashcard view
- [ ] Sync progress with SRS system
- [ ] Add keyboard navigation (arrows to move, Enter to select)
- [ ] Persist last viewed region

### Phase 05: Polish & Testing

- [ ] Add entrance animations for nodes
- [ ] Sound effects (optional, can disable)
- [ ] Performance optimization for 189 nodes
- [ ] Integration tests with GrammarTab
- [ ] User acceptance testing

---

## Quick Commands

```
/code phase-01    # Start Phase 1
/next             # Check progress
/save-brain       # Save context
```

---

## Files to Create

```
frontend/
├── models/
│   └── learning_progress.py     # Progress model
├── services/
│   └── learning_map_service.py  # Progress & map logic
├── ui/
│   └── widgets/
│       ├── learning_map/
│       │   ├── __init__.py
│       │   ├── map_widget.py    # Main container
│       │   ├── map_scene.py     # QGraphicsScene
│       │   ├── map_view.py      # QGraphicsView
│       │   ├── grammar_node.py  # Node component
│       │   ├── path_line.py     # Connection lines
│       │   └── region_bg.py     # Background graphics
│       └── ...
```

---

## Design Decisions

1. **QGraphicsView vs Custom Paint:** Chọn QGraphicsView vì hỗ trợ zoom/pan sẵn, dễ handle click events
2. **Node Layout:** Sử dụng force-directed layout hoặc pre-defined positions per region
3. **Progress Storage:** Extend existing `user_progress` table thay vì tạo table mới
