# Gamification Upgrade Phase 1: Vocabulary Tinder Mode

## Objective

Implement "Tinder for Words" (Lướt từ) in the Vocabulary Tab to provide a rapid-fire review mode.

## Features

- **Tinder Card Dashboard**: Add a new "Lướt từ" card in the Smart Dashboard.
- **Tinder View**: A new review interface optimized for speed.
  - Big flashcard.
  - "Swipe Left" (Red - Again) and "Swipe Right" (Green - Good) actions.
  - Simple animations for card transition.
- **Logic**:
  - Fetches a mix of New and Review items.
  - Simple 2-button grading (Pass/Fail) mapped to SRS.

## Implementation Steps

- [ ] **Step 1: Dashboard UI Update**
  - Update `_create_smart_dashboard` in `vocab_tab.py` to add the "Lướt từ" card.
  - Apply hover effects to all dashboard cards.
- [ ] **Step 2: Tinder View Component**
  - Create `TinderCardView` (simplified FlashcardView).
  - Create `TinderSessionWidget` containing the card and controls.
- [ ] **Step 3: Integration**
  - Add `tinder_view_widget` to `VocabTab.stacked_widget`.
  - Implement `_start_tinder_session` logic.
- [ ] **Step 4: Animation & Polish**
  - Add slide animations for feedback.
