# Phase 02: Map Widget Core

**Status:** ⬜ Pending
**Dependencies:** Phase 01 (Data Layer)
**Est. Time:** 4-5 hours

---

## Objective

Tạo widget chính hiển thị bản đồ Fantasy với các vùng đất, hỗ trợ zoom/pan và chuyển đổi giữa các vùng.

---

## Tasks

### 1. Create LearningMapWidget Container

- [ ] Main QWidget containing all map components
- [ ] Layout: MapView (center) + Minimap (corner) + Controls (top)
- [ ] Region selector toolbar

### 2. Create MapScene (QGraphicsScene)

- [ ] Set scene rect for full map (5 regions)
- [ ] Add region background images
- [ ] Define node positions per region
- [ ] Handle item z-ordering (bg → paths → nodes)

### 3. Create MapView (QGraphicsView)

- [ ] Enable drag-to-pan (setDragMode)
- [ ] Enable scroll-to-zoom
- [ ] Smooth zoom transitions (animate scale)
- [ ] Fit-to-region on double-click

### 4. Design Region Backgrounds

- [ ] A1 "Đảo Khởi Đầu": Beach/island theme (cyan/green gradient)
- [ ] A2 "Rừng Sơ Cấp": Forest theme (green/dark green)
- [ ] B1 "Núi Trung Cấp": Mountain theme (grey/white)
- [ ] B2 "Núi Lửa Nâng Cao": Volcano theme (red/orange)
- [ ] C1 "Lâu Đài Master": Castle theme (purple/gold)

### 5. Implement Region Switching

- [ ] Click region in toolbar → smooth pan to region
- [ ] Keyboard shortcuts (1-5 for regions)
- [ ] Visual indicator of current region

### 6. Add Minimap Overlay

- [ ] Small map in corner showing full overview
- [ ] Highlight current viewport
- [ ] Click minimap to jump to location

### 7. Smooth Zoom Animations

- [ ] Animate zoom level changes (QPropertyAnimation)
- [ ] Zoom limits (min 50%, max 200%)
- [ ] Zoom to cursor position

### 8. Add Region Labels

- [ ] Floating region name labels
- [ ] Progress indicator per region (e.g., "15/30 ✅")
- [ ] Visual unlock status (greyed out if locked)

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/ui/widgets/learning_map/__init__.py` | CREATE | Package init |
| `frontend/ui/widgets/learning_map/map_widget.py` | CREATE | Main container |
| `frontend/ui/widgets/learning_map/map_scene.py` | CREATE | QGraphicsScene |
| `frontend/ui/widgets/learning_map/map_view.py` | CREATE | QGraphicsView |
| `frontend/ui/widgets/learning_map/region_bg.py` | CREATE | Region backgrounds |
| `frontend/ui/widgets/learning_map/minimap.py` | CREATE | Minimap overlay |
| `assets/images/map/` | CREATE | Region background images |

---

## Visual Layout

```
┌───────────────────────────────────────────────────┐
│  [A1] [A2] [B1] [B2] [C1]   🔍 Zoom: 100%   │  ← Toolbar
├───────────────────────────────────────────────────┤
│                                          ┌─────┐ │
│                                          │ 📍  │ │  ← Minimap
│           🗺️ MAP VIEW                   │     │ │
│                                          └─────┘ │
│            (zoomable, pannable)                  │
│                                                  │
└───────────────────────────────────────────────────┘
```

---

## Test Criteria

- [ ] Map loads without lag (< 500ms)
- [ ] Zoom works smoothly (30+ fps)
- [ ] Can pan to all regions
- [ ] Minimap updates on pan
- [ ] Region buttons switch view correctly

---

**Next Phase:** [Phase 03 - Node Components](phase-03-node-components.md)
