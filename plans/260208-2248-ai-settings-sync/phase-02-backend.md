# Phase 02: Core Service Synchronization

Status: ⬜ Pending
Dependencies: Phase 01

## Objective

Đồng bộ logic xử lý API Key và Model Waterfall trong `ai_service.py`.

## Implementation Steps

1. [ ] Cập nhật `AIConfigManager` để hỗ trợ `api_keys` list.
2. [x] Đồng bộ logic `rotate_api_key` và `generate_response` (Waterfall).
3. [ ] Cập nhật legacy SDK fallback.

## Files to Create/Modify

- `frontend/services/ai_service.py` - Modify
