# Phase 05: Progress Dashboard

**Status:** ⬜ Pending
**Dependencies:** Phase 02, 03, 04
**Est. Time:** 3 hours

---

## Objective

Xây dựng Dashboard theo dõi tiến độ học TOEIC:

- Thống kê tổng quan
- Biểu đồ tiến độ
- Điểm dự đoán
- Đề xuất học tập

---

## Requirements

### Dashboard Widgets

1. **Overview Stats**
   - Tổng số từ vựng đã học
   - Số câu Listening đã làm
   - Số câu Reading đã làm
   - Tỷ lệ đúng TB

2. **Progress Chart**
   - Line chart: Accuracy theo ngày
   - Bar chart: Số câu làm theo part
   - Pie chart: Phân bố thời gian học

3. **Estimated Score**
   - Listening: xxx/495
   - Reading: xxx/495
   - Total: xxx/990
   - Target: 720

4. **Weak Points**
   - Top 3 grammar topics cần ôn
   - Top 3 listening types kém nhất

5. **Study Streak**
   - Số ngày liên tiếp học
   - Calendar heatmap

---

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│  📊 TOEIC PROGRESS DASHBOARD                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │   320   │ │   150   │ │   200   │ │   72%   │   │
│  │  Words  │ │  LC Q's │ │  RC Q's │ │ Accuracy│   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│                                                     │
│  ┌─────────────────────┐ ┌─────────────────────┐   │
│  │  📈 ACCURACY TREND  │ │  🎯 ESTIMATED SCORE │   │
│  │                     │ │                     │   │
│  │    ╱‾‾‾╲            │ │  Listening:  340    │   │
│  │   ╱    ╲___         │ │  Reading:    320    │   │
│  │  ╱                  │ │  ─────────────────  │   │
│  │ Feb 1    Feb 5      │ │  Total:      660    │   │
│  └─────────────────────┘ │  Target:     720    │   │
│                         └─────────────────────┘   │
│  ┌─────────────────────┐ ┌─────────────────────┐   │
│  │  ⚠️ WEAK POINTS     │ │  🔥 STUDY STREAK    │   │
│  │                     │ │                     │   │
│  │  ❌ Verb Tense      │ │  5 days in a row!   │   │
│  │  ❌ Part 3 (Conv)   │ │  🟩🟩🟩🟩🟩⬜⬜      │   │
│  │  ❌ Prepositions    │ │                     │   │
│  └─────────────────────┘ └─────────────────────┘   │
│                                                     │
│  [📚 Start Today's Session]                        │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Steps

1. [ ] Tạo `frontend/ui/tabs/toeic_dashboard_tab.py`
2. [ ] Add stats calculation in `toeic_service.py`
3. [ ] Create chart widgets (matplotlib hoặc pyqtgraph)
4. [ ] Implement estimated score algorithm
5. [ ] Add weak point detection
6. [ ] Add study streak tracking

---

## Estimated Score Algorithm

```python
def calculate_estimated_score(user_id):
    # Lấy accuracy từ 50 câu gần nhất
    lc_accuracy = get_recent_accuracy(user_id, part=[1,2,3,4], limit=50)
    rc_accuracy = get_recent_accuracy(user_id, part=[5,6,7], limit=50)
    
    # TOEIC score = 5 + (accuracy * 490)
    lc_score = int(5 + lc_accuracy * 490)
    rc_score = int(5 + rc_accuracy * 490)
    
    return lc_score, rc_score, lc_score + rc_score
```

---

## Files to Create

- `frontend/ui/tabs/toeic_dashboard_tab.py` - Dashboard UI
- `frontend/ui/widgets/stat_card.py` - Stat card widget
- `frontend/ui/widgets/progress_chart.py` - Chart widget

---

## Test Criteria

- [ ] Stats display correctly
- [ ] Charts render without error
- [ ] Estimated score updates after practice
- [ ] Weak points detected accurately
- [ ] Streak counts correctly

---

**MVP Complete!** 🎉
