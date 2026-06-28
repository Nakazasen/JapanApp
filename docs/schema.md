# Database Schema

## Overview

The application uses **SQLite** with **SQLModel** (SQLAlchemy) for data persistence. The schema is designed for multi-language scalability.

---

## Tables

### 1. `unified_vocab_items`

Consolidated table for vocabulary across all languages.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Unique identifier |
| `user_id` | Integer | Link to user |
| `term` | String | The word/phrase (e.g., "Cat", "猫") |
| `reading` | String | IPA (EN), Kana (JP), etc. |
| `meaning` | String | Primary Vietnamese meaning |
| `lang` | String | Language code ("en", "jp", "kr") |
| `level` | String | Proficiency level (N1, B2) |
| `source_material` | String | Source curriculum |
| `topic_id` | Integer | Foreign key to `VocabTopic` |
| `mastery_status` | String | new, learning, hard, mastered |
| `meta_data` | JSON | Language-specific fields (han_viet, romaji, ipa, pos) |
| `examples` | JSON | List of `{"sentence": "...", "translation": "..."}` |
| `tags` | String | User-defined tags |
| `user_note` | Text | Personal notes |
| `srs_level` | Integer | Current SRS stage |
| `next_review` | DateTime | Next scheduled study time |

### 2. `vocab_topics`

Decks or categories for vocabulary items.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier |
| `name` | String | Name of the topic/category |
| `description` | String | Description of the topic |
| `created_at` | DateTime | Creation timestamp |

---

## Relationships

- **One-to-Many**: `vocab_topics` -> `unified_vocab_items` (via `topic_id`).
- **One-to-Many**: `users` -> `unified_vocab_items` (via `user_id`).
