"""Toast Helper - Simple utility for showing toast notifications.

Enterprise UX: Replace QMessageBox with non-blocking toasts.

Usage:
    from frontend.utils.toast_helper import toast_success, toast_error, toast_info
    
    # Simple usage
    toast_success("Đã lưu thành công!")
    toast_error("Có lỗi xảy ra!")
    
    # With action button
    toast_error("Lưu thất bại!", action_text="Thử lại", action_callback=save_again)
"""
from typing import Optional, Callable


def _get_toast():
    """Get toast manager instance."""
    from frontend.ui.widgets.toast_widget import get_toast_manager
    return get_toast_manager()


def toast_success(
    message: str, 
    duration_ms: int = 4000,
    action_text: Optional[str] = None,
    action_callback: Optional[Callable] = None
):
    """Show success toast notification.
    
    Args:
        message: Message to display
        duration_ms: Auto-dismiss time (default 4 seconds)
        action_text: Optional action button text
        action_callback: Optional callback when action clicked
    """
    _get_toast().show_success(message, duration_ms, action_text, action_callback)


def toast_error(
    message: str, 
    duration_ms: int = 5000,
    action_text: Optional[str] = None,
    action_callback: Optional[Callable] = None
):
    """Show error toast notification.
    
    Args:
        message: Error message
        duration_ms: Auto-dismiss time (default 5 seconds)
        action_text: Optional action button (e.g., "Retry")
        action_callback: Optional callback when action clicked
    """
    _get_toast().show_error(message, duration_ms, action_text, action_callback)


def toast_warning(
    message: str, 
    duration_ms: int = 4500,
    action_text: Optional[str] = None,
    action_callback: Optional[Callable] = None
):
    """Show warning toast notification."""
    _get_toast().show_warning(message, duration_ms, action_text, action_callback)


def toast_info(
    message: str, 
    duration_ms: int = 4000,
    action_text: Optional[str] = None,
    action_callback: Optional[Callable] = None
):
    """Show info toast notification."""
    _get_toast().show_info(message, duration_ms, action_text, action_callback)
