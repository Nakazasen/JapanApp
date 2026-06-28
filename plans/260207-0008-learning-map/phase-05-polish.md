# Phase 05: Polish & Testing

**Status:** ⬜ Pending
**Dependencies:** Phase 04 (Integration)
**Est. Time:** 2-3 hours

---

## Objective

Hoàn thiện trải nghiệm người dùng với animations, sound effects (optional), và đảm bảo performance tốt với 189 nodes.

---

## Tasks

### 1. Add Entrance Animations

- [ ] Nodes fade in sequentially when region loads
- [ ] "Unlock" animation when node becomes available
- [ ] Celebration effect when node mastered

### 2. Sound Effects (Optional)

- [ ] Node click sound
- [ ] Unlock sound
- [ ] Mastery fanfare
- [ ] Add toggle in settings to disable

### 3. Performance Optimization

- [ ] Lazy load nodes outside viewport
- [ ] Use item caching for QGraphicsItems
- [ ] Profile and optimize hot paths
- [ ] Target: < 100ms initial load, 60fps scrolling

### 4. Integration Tests

- [ ] Test map loads with real grammar data (189 items)
- [ ] Test progress persistence across sessions
- [ ] Test edge cases (all locked, all mastered)
- [ ] Test memory usage over extended use

### 5. User Acceptance Criteria

- [ ] Map is intuitive without instructions
- [ ] Progress is clearly visible
- [ ] Navigation feels smooth and responsive
- [ ] Visual style matches Fantasy theme

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/ui/widgets/learning_map/animations.py` | CREATE | Animation helpers |
| `frontend/ui/widgets/learning_map/sounds.py` | CREATE | Sound effects |
| `tests/test_learning_map_integration.py` | CREATE | Integration tests |

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Initial load | < 500ms | Time from tab switch to map visible |
| Scroll FPS | 60 fps | During pan/zoom |
| Memory | < 100MB | After 30 min use |
| Node render | < 1ms each | Individual node paint time |

---

## Animation Specs

### Node Unlock

```
Duration: 500ms
Effect: Scale 0 → 1.2 → 1 + glow pulse
Sound: "unlock.wav" (optional)
```

### Node Mastery

```
Duration: 800ms
Effect: Star burst particles + golden glow
Sound: "fanfare.wav" (optional)
```

### Region Transition

```
Duration: 300ms
Effect: Smooth pan + slight zoom out/in
Easing: ease-in-out
```

---

## Test Criteria

- [ ] All animations run at 60fps
- [ ] Sounds play correctly (when enabled)
- [ ] App doesn't lag with 189 nodes
- [ ] Tests pass on CI
- [ ] User feedback is positive

---

## 🎉 Completion Checklist

After Phase 05, verify:

- [ ] Learning Map is accessible from Grammar Tab
- [ ] All 189 grammar items appear as nodes
- [ ] Progress is tracked and persisted
- [ ] Visual theme is Fantasy RPG
- [ ] Performance meets targets
- [ ] No critical bugs

---

**MVP COMPLETE! 🚀**

Ready for Phase 2 features:

- Sentence Builder
- Boss Node challenges
- Achievement badges
