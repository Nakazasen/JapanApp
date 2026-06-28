# Phase 01: Data Layer & Progress Model

**Status:** ⬜ Pending
**Dependencies:** None
**Est. Time:** 2-3 hours

---

## Objective

Tạo foundation cho Learning Map: model lưu progress, service xử lý logic, và helper phân nhóm grammar theo vùng.

---

## Tasks

### 1. Create LearningProgress Model

- [ ] Define `LearningProgress` SQLModel class
- [ ] Fields: `id`, `grammar_id`, `status`, `attempts`, `mastered_at`, `last_studied`
- [ ] Status enum: `LOCKED`, `AVAILABLE`, `LEARNING`, `MASTERED`

### 2. Create MapRegion Enum

- [ ] Define regions: A1, A2, B1, B2, C1
- [ ] Add display names (Vietnamese): "Đảo Khởi Đầu", "Rừng Sơ Cấp", etc.
- [ ] Add color schemes for each region

### 3. Group Grammar by Region

- [ ] Create helper function to categorize grammar items
- [ ] Map existing `level` field to `MapRegion`
- [ ] Handle edge cases (no level, mixed levels)

### 4. Create Progress Service

- [ ] `get_progress(grammar_id)` → current status
- [ ] `update_progress(grammar_id, new_status)`
- [ ] `get_region_stats(region)` → % complete, total/mastered
- [ ] `unlock_next_nodes(grammar_id)` → unlock dependent nodes

### 5. Database Migration

- [ ] Add `region` column to grammar table (if needed)
- [ ] Create `learning_progress` table
- [ ] Seed initial progress (all A1 items = AVAILABLE, rest = LOCKED)

### 6. Unit Tests

- [ ] Test progress CRUD operations
- [ ] Test region grouping logic
- [ ] Test unlock chain logic

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/models/learning_progress.py` | CREATE | Progress model |
| `frontend/services/learning_map_service.py` | CREATE | Business logic |
| `backend/scripts/migrate_learning_map.py` | CREATE | DB migration |
| `tests/test_learning_progress.py` | CREATE | Unit tests |

---

## Code Snippets

### LearningProgress Model

```python
from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime

class ProgressStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    LEARNING = "learning"
    MASTERED = "mastered"

class LearningProgress(SQLModel, table=True):
    __tablename__ = "learning_progress"
    
    id: int = Field(default=None, primary_key=True)
    grammar_id: int = Field(foreign_key="grammar_topics.id")
    status: ProgressStatus = Field(default=ProgressStatus.LOCKED)
    attempts: int = Field(default=0)
    mastered_at: datetime | None = None
    last_studied: datetime | None = None
```

---

## Test Criteria

- [ ] Can create/read/update progress records
- [ ] Region grouping returns correct counts
- [ ] Unlocking A1 item unlocks next A1 item
- [ ] Completing all A1 unlocks first A2 item

---

**Next Phase:** [Phase 02 - Map Widget Core](phase-02-map-widget.md)
