# Phase 03: Node Components

**Status:** ⬜ Pending
**Dependencies:** Phase 02 (Map Widget Core)
**Est. Time:** 3-4 hours

---

## Objective

Tạo các node đại diện cho từng cấu trúc ngữ pháp, với visual states và interactions.

---

## Tasks

### 1. Create GrammarNode (QGraphicsItem)

- [ ] Base node class for grammar items
- [ ] Store grammar_id, title, status
- [ ] Handle mouse events (click, hover)
- [ ] Emit signals on interaction

### 2. Implement Node Visual States

- [ ] **LOCKED** 🔒: Dark, desaturated, lock icon
- [ ] **AVAILABLE** ⬜: Dim but visible, glow effect
- [ ] **LEARNING** 🔵: Bright, pulsing animation
- [ ] **MASTERED** ✅: Full color, star badge

### 3. Add Progress Ring

- [ ] Circular progress indicator around node
- [ ] Shows study progress (0-100%)
- [ ] Color changes based on progress
- [ ] Animate on update

### 4. Create Path Lines

- [ ] Connect related nodes
- [ ] Bezier curves for smooth paths
- [ ] Style based on locked/unlocked
- [ ] Animate "unlock" effect

### 5. Node Click → Study View

- [ ] Click AVAILABLE/LEARNING → open flashcard
- [ ] Click LOCKED → show tooltip "Complete X first"
- [ ] Click MASTERED → option to review

### 6. Add Hover Tooltips

- [ ] Show grammar title
- [ ] Show brief description
- [ ] Show current status & progress

### 7. Create Boss Node Variant

- [ ] Larger size (1.5x normal)
- [ ] Crown/special icon
- [ ] Gate to next region
- [ ] Special challenge on click

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/ui/widgets/learning_map/grammar_node.py` | CREATE | Node component |
| `frontend/ui/widgets/learning_map/path_line.py` | CREATE | Connection lines |
| `frontend/ui/widgets/learning_map/node_tooltip.py` | CREATE | Hover tooltips |
| `frontend/ui/widgets/learning_map/boss_node.py` | CREATE | Boss node variant |

---

## Visual Design

### Normal Node

```
     ╭─────────╮
     │  ○ 75%  │  ← Progress ring
     │   📘    │  ← Icon (changes by status)
     │ "N+の"  │  ← Grammar title
     ╰─────────╯
```

### Boss Node

```
     ╭───────────────╮
     │     👑        │  ← Crown
     │   ⭐ 100%     │  ← Larger ring
     │    🏆        │  ← Trophy icon
     │ "A1 BOSS"   │
     ╰───────────────╯
```

---

## Node States Visual

| State | Background | Border | Icon | Effect |
|-------|------------|--------|------|--------|
| LOCKED | #2d2d2d | #555 | 🔒 | Desaturated |
| AVAILABLE | #3a506b | #5bc0be | ⬜ | Subtle glow |
| LEARNING | #0b132b | #6fffe9 | 🔵 | Pulse animation |
| MASTERED | #1a535c | #ffd166 | ⭐ | Star badge |

---

## Test Criteria

- [ ] All 4 states render correctly
- [ ] Click events fire properly
- [ ] Progress ring updates on data change
- [ ] Paths connect correct nodes
- [ ] Boss nodes are visually distinct

---

**Next Phase:** [Phase 04 - Integration & Navigation](phase-04-integration.md)
