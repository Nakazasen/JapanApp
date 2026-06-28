"""Base service module - Simplified for local desktop app.

Provides base error class and common utilities.
No more HTTP client since we're using direct database access.
"""
from typing import Optional


class ServiceError(Exception):
    """Custom exception for service errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# Keep APIError as alias for backward compatibility
APIError = ServiceError


class BaseService:
    """Base class for local services.
    
    In the desktop-only architecture, services interact directly with:
    - SQLite database via SQLModel
    - Gemini API for AI features
    - Local file system for data
    """
    
    # Current user ID (shared across services)
    _current_user_id: Optional[int] = None
    
    @classmethod
    def set_current_user(cls, user_id: int):
        """Set current user ID for all services."""
        cls._current_user_id = user_id
    
    @classmethod
    def get_current_user_id(cls) -> Optional[int]:
        """Get current user ID."""
        return cls._current_user_id
    
    @classmethod
    def clear_current_user(cls):
        """Clear current user."""
        cls._current_user_id = None
