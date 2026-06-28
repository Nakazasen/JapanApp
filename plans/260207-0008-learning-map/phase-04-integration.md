# Phase 04: Integration & Navigation

**Status:** ⬜ Pending
**Dependencies:** Phase 03 (Node Components)
**Est. Time:** 2-3 hours

---

## Objective

Tích hợp Learning Map vào Grammar Tab hiện tại, đồng bộ với flashcard view và SRS system.

---

## Tasks

### 1. Add Map View Toggle to GrammarTab

- [ ] Add toggle button in toolbar: "List View" ↔ "Map View"
- [ ] Show/hide appropriate widget based on mode
- [ ] Remember last used view mode

### 2. Connect Map Selection to Flashcard View

- [ ] On node click → open existing `GrammarFlashcardView`
- [ ] Pass grammar_id to flashcard
- [ ] Return to map on flashcard close

### 3. Sync Progress with SRS System

- [ ] When flashcard completed → update LearningProgress
- [ ] Use existing SRS difficulty ratings
- [ ] Map SRS ease to progress status:
  - 1-2 stars → LEARNING
  - 3-4 stars → MASTERED

### 4. Keyboard Navigation

- [ ] Arrow keys to move between nodes
- [ ] Enter to open selected node
- [ ] Escape to close flashcard and return to map
- [ ] Number keys 1-5 to jump to regions

### 5. Persist Last Viewed Region

- [ ] Save current region to settings
- [ ] Restore on app reopen
- [ ] Optional: save zoom level too

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/ui/tabs/grammar_tab.py` | MODIFY | Add map view toggle |
| `frontend/ui/widgets/learning_map/map_widget.py` | MODIFY | Add navigation signals |
| `frontend/services/learning_map_service.py` | MODIFY | Add SRS sync logic |

---

## Integration Points

```
┌─────────────────────────────────────────────────────────┐
│                     GrammarTab                          │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│  ┌────────────────┐  │  ┌────────────────────────────┐ │
│  │   List View    │  │  │       Map View             │ │
│  │  (existing)    │◄─┼─►│    (new widget)            │ │
│  └────────────────┘  │  └─────────────┬──────────────┘ │
│         │            │                │                │
│         ▼            │                ▼                │
│  ┌────────────────┐  │  ┌────────────────────────────┐ │
│  │ FlashcardView  │◄─┼──┤   Click Node               │ │
│  │  (existing)    │  │  └────────────────────────────┘ │
│  └────────────────┘  │                                 │
│         │            │                                 │
│         ▼            │                                 │
│  ┌────────────────┐  │                                 │
│  │ SRS + Progress │◄─┼─────────── Sync ────────────────┤
│  └────────────────┘  │                                 │
└──────────────────────┴─────────────────────────────────┘
```

---

## Test Criteria

- [ ] Toggle between list/map works smoothly
- [ ] Clicking node opens correct grammar item
- [ ] Progress updates after flashcard completion
- [ ] Keyboard navigation works in map view
- [ ] Last region is restored on app reopen

---

**Next Phase:** [Phase 05 - Polish & Testing](phase-05-polish.md)
