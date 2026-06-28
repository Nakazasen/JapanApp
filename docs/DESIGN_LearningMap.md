# 🎨 DESIGN: Learning Map (Bản đồ Chinh phục Ngữ pháp)

**Ngày tạo:** 2026-02-07
**Dựa trên:** [plan.md](file:///c:/ProgramData/Sandbox/Projects/EnglishApp/plans/260207-0008-learning-map/plan.md)

---

## 1. Cách Lưu Thông Tin (Database Schema)

### 1.1. Sơ đồ quan hệ

```
┌─────────────────────────────────────────────────────────────────┐
│  📘 GRAMMAR_TOPICS (Đã có - 189 items)                          │
│  ├── id, title, pattern, description                            │
│  ├── level: "A1" | "A2" | "B1" | "B2" | "C1"  ← Region mapping  │
│  ├── mastery_status: new | learning | mastered | hard           │
│  └── srs_level, srs_ease_factor, next_review_at (SRS data)      │
└───────────────────────────┬─────────────────────────────────────┘
                            │ 1 grammar → 1 progress record
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  🗺️ LEARNING_PROGRESS (Mới - Map-specific progress)            │
│  ├── id (PK)                                                    │
│  ├── grammar_id (FK → grammar_topics.id)                        │
│  ├── map_status: LOCKED | AVAILABLE | LEARNING | MASTERED       │
│  ├── position_x, position_y (vị trí node trên map)              │
│  ├── unlocked_at, mastered_at (timestamps)                      │
│  └── is_boss_node: bool (node boss cuối vùng)                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2. Model mới: LearningProgress

```python
class MapStatus(str, Enum):
    LOCKED = "locked"       # 🔒 Chưa mở khóa
    AVAILABLE = "available" # ⬜ Có thể học
    LEARNING = "learning"   # 🔵 Đang học
    MASTERED = "mastered"   # ✅ Đã thành thạo

class LearningProgress(SQLModel, table=True):
    __tablename__ = "learning_progress"
    
    id: int = Field(primary_key=True)
    grammar_id: int = Field(foreign_key="grammar_topics.id", unique=True)
    
    # Map-specific fields
    map_status: MapStatus = Field(default=MapStatus.LOCKED)
    position_x: float = Field(default=0.0)  # Node X position
    position_y: float = Field(default=0.0)  # Node Y position
    is_boss_node: bool = Field(default=False)
    
    # Progress timestamps
    unlocked_at: datetime | None = None
    mastered_at: datetime | None = None
    
    # Dependencies (which nodes must be completed first)
    prerequisite_ids: str | None = None  # Comma-separated IDs
```

### 1.3. Region Mapping

```python
class MapRegion(str, Enum):
    A1 = "a1"  # 🏝️ Đảo Khởi Đầu
    A2 = "a2"  # 🌲 Rừng Sơ Cấp
    B1 = "b1"  # 🏔️ Núi Trung Cấp
    B2 = "b2"  # 🌋 Núi Lửa Nâng Cao
    C1 = "c1"  # 🏰 Lâu Đài Master

REGION_CONFIG = {
    MapRegion.A1: {
        "name": "Đảo Khởi Đầu",
        "icon": "🏝️",
        "color_primary": "#4ecdc4",  # Cyan
        "color_secondary": "#a8e6cf",  # Light green
        "unlock_condition": None,  # Always available
    },
    MapRegion.A2: {
        "name": "Rừng Sơ Cấp",
        "icon": "🌲",
        "color_primary": "#2d5016",  # Dark green
        "color_secondary": "#6b8e23",  # Olive
        "unlock_condition": "complete_a1_boss",
    },
    # ... etc
}

def get_region_from_level(level: str) -> MapRegion:
    """Map grammar level to map region."""
    mapping = {
        "A1": MapRegion.A1,
        "A2": MapRegion.A2,
        "B1": MapRegion.B1,
        "B2": MapRegion.B2,
        "C1": MapRegion.C1,
        "C2": MapRegion.C1,  # Merge C2 into C1
    }
    return mapping.get(level, MapRegion.A1)
```

---

## 2. Danh Sách Màn Hình / Components

### 2.1. Component Hierarchy

```
LearningMapWidget (QWidget)
├── MapToolbar (QToolBar)
│   ├── RegionButton x5 (A1, A2, B1, B2, C1)
│   ├── ZoomSlider
│   └── ProgressLabel ("15/189 ✅")
├── MapView (QGraphicsView)
│   └── MapScene (QGraphicsScene)
│       ├── RegionBackground x5
│       ├── PathLine (connections between nodes)
│       └── GrammarNode x189
│           ├── NodeCircle (visual)
│           ├── ProgressRing
│           ├── StatusIcon (🔒/⬜/🔵/✅)
│           └── TitleLabel
└── MiniMapOverlay (QWidget)
```

### 2.2. Component Specs

| Component | Kích thước | Chức năng |
|-----------|-----------|-----------|
| `LearningMapWidget` | Full tab | Container chính |
| `MapToolbar` | 50px height | Điều hướng vùng |
| `MapView` | Flexible | Zoom/pan bản đồ |
| `GrammarNode` | 60x60 px | Đại diện 1 cấu trúc |
| `PathLine` | 3px stroke | Nối các node |
| `MiniMapOverlay` | 150x100 px | Tổng quan + jump |

---

## 3. Luồng Hoạt Động (User Flows)

### 3.1. Lần đầu mở Map

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 FLOW 1: First Time Experience
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ User clicks "🗺️ Map View" in GrammarTab
2️⃣ System checks: Has progress data?
   └── NO → Seed initial progress (A1 items = AVAILABLE)
3️⃣ Map loads, zooms to Region A1
4️⃣ First 3-5 nodes glow (AVAILABLE state)
5️⃣ Tutorial tooltip: "Click a node to start learning!"
```

### 3.2. Học một Grammar Node

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 FLOW 2: Study a Grammar Node
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ User clicks an AVAILABLE/LEARNING node
2️⃣ Node pulses → Opens GrammarFlashcardView
3️⃣ User studies flashcard, rates difficulty (1-4)
4️⃣ On close:
   ├── Rating 1-2 → Status stays LEARNING
   └── Rating 3-4 → Status → MASTERED
5️⃣ Map updates:
   ├── Current node glows with star (if mastered)
   └── Next node unlocks (LOCKED → AVAILABLE)
6️⃣ Progress bar updates
```

### 3.3. Hoàn thành vùng (Boss Fight)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 FLOW 3: Complete a Region
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ User masters all nodes in A1
2️⃣ Boss Node unlocks (last node in region)
3️⃣ User clicks Boss Node
4️⃣ Challenge: Review quiz (5 random A1 items)
5️⃣ Pass (≥80%) → 
   ├── 🎉 Celebration animation
   ├── A2 region unlocks (first 3-5 nodes)
   └── Achievement badge awarded
6️⃣ Map pans to A2 region
```

---

## 4. Node Positioning Algorithm

### 4.1. Layout Strategy

Each region has nodes arranged in a **spiral/path pattern**:

```python
def calculate_node_positions(grammar_items: list, region: MapRegion) -> dict:
    """Calculate X,Y positions for nodes in a region."""
    
    # Region bounds
    REGION_WIDTH = 800
    REGION_HEIGHT = 600
    NODE_SPACING = 80
    
    positions = {}
    items = [g for g in grammar_items if get_region_from_level(g.level) == region]
    
    # Spiral layout from center
    center_x, center_y = REGION_WIDTH / 2, REGION_HEIGHT / 2
    angle = 0
    radius = 50
    
    for i, item in enumerate(items):
        x = center_x + radius * cos(angle)
        y = center_y + radius * sin(angle)
        positions[item.id] = (x, y)
        
        angle += 0.5  # Rotate
        if i % 5 == 0:
            radius += 30  # Expand outward
    
    return positions
```

---

## 5. Test Cases

### 5.1. Data Layer Tests

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TC-01: Initial Progress Seeding
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Given: Fresh database with 189 grammar items
When:  LearningMapService.seed_progress() is called
Then:  ✓ 189 LearningProgress records created
       ✓ A1 items → status = AVAILABLE
       ✓ A2-C1 items → status = LOCKED
       ✓ Boss nodes marked correctly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TC-02: Progress Update → Unlock Next
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Given: Node #1 is AVAILABLE, Node #2 is LOCKED
When:  User masters Node #1
Then:  ✓ Node #1 → MASTERED
       ✓ Node #2 → AVAILABLE
       ✓ mastered_at timestamp set

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TC-03: Region Completion → Unlock Next Region
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Given: All A1 nodes mastered except Boss Node
When:  User completes A1 Boss Node
Then:  ✓ A2 first 3-5 nodes → AVAILABLE
       ✓ Region progress = 100%
```

### 5.2. UI Tests

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TC-04: Map Loads < 500ms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Given: GrammarTab is open
When:  User clicks "Map View" toggle
Then:  ✓ Map visible within 500ms
       ✓ All 189 nodes rendered
       ✓ No frame drops (60fps)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TC-05: Node Click Opens Flashcard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Given: Map is displayed, Node #5 is AVAILABLE
When:  User clicks Node #5
Then:  ✓ GrammarFlashcardView opens
       ✓ Correct grammar item loaded
       ✓ Map stays in background

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TC-06: LOCKED Node Shows Tooltip
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Given: Map is displayed, Node #50 is LOCKED
When:  User clicks Node #50
Then:  ✓ No flashcard opens
       ✓ Tooltip shows "Complete [prerequisite] first"
```

---

## 6. Visual Theme Reference

### Color Palette

| Region | Primary | Secondary | Accent |
|--------|---------|-----------|--------|
| A1 🏝️ | `#4ecdc4` | `#a8e6cf` | `#ffd93d` |
| A2 🌲 | `#2d5016` | `#6b8e23` | `#98d8c8` |
| B1 🏔️ | `#6c757d` | `#adb5bd` | `#74b9ff` |
| B2 🌋 | `#d63031` | `#ff7675` | `#fdcb6e` |
| C1 🏰 | `#6c5ce7` | `#a29bfe` | `#ffeaa7` |

### Node States

| State | Fill | Stroke | Icon | Effect |
|-------|------|--------|------|--------|
| LOCKED | `#2d3436` | `#636e72` | 🔒 | Opacity 40% |
| AVAILABLE | `#2d3436` | `#00cec9` | ⬜ | Glow pulse |
| LEARNING | `#0984e3` | `#74b9ff` | 🔵 | Breathing anim |
| MASTERED | `#00b894` | `#55efc4` | ⭐ | Star badge |

---

## 7. Next Steps

- [ ] `/visualize` - Xem mockup UI
- [ ] `/code phase-01` - Bắt đầu code Data Layer

---

*Tạo bởi AWF 2.1 - Design Phase*
