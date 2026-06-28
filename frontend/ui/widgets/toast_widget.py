"""Toast Notification Widget - Enterprise Edition.

Provides non-blocking toast notifications for user feedback.
Supports success, error, warning, and info message types.

Enterprise Features:
- Action buttons (Undo, Retry, etc.)
- Slide-in animations
- UI event logging
"""
from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, 
    QGraphicsOpacityEffect, QPushButton, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, Signal
from PySide6.QtGui import QColor, QFont
from typing import Optional, List, Callable
from enum import Enum
import logging

# Setup logger for UI events (Enterprise audit trail)
ui_logger = logging.getLogger("ui.toast")
ui_logger.setLevel(logging.INFO)


class ToastType(Enum):
    """Toast notification types."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ToastWidget(QWidget):
    """Single toast notification widget with optional action button.
    
    Enterprise Features:
    - Action button for quick actions (Undo, Retry, etc.)
    - Slide-in animation from right edge
    - Fade animations
    """
    
    # Signal emitted when action button is clicked
    action_clicked = Signal()
    
    STYLES = {
        ToastType.SUCCESS: {
            "bg": "#2ecc71",
            "icon": "✅",
            "border": "#27ae60"
        },
        ToastType.ERROR: {
            "bg": "#e74c3c",
            "icon": "❌",
            "border": "#c0392b"
        },
        ToastType.WARNING: {
            "bg": "#f39c12",
            "icon": "⚠️",
            "border": "#d68910"
        },
        ToastType.INFO: {
            "bg": "#3498db",
            "icon": "ℹ️",
            "border": "#2980b9"
        }
    }
    
    def __init__(
        self, 
        message: str, 
        toast_type: ToastType = ToastType.INFO,
        duration_ms: int = 4000,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        self.duration_ms = duration_ms
        self.action_text = action_text
        self.action_callback = action_callback
        self._start_x = 0
        self._target_x = 0
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self._setup_ui()
        self._setup_animations()
        
        # Log toast creation for audit trail
        ui_logger.info(f"Toast created: type={toast_type.value}, message='{message[:50]}...'")
        
    def _setup_ui(self):
        """Setup the toast UI with optional action button."""
        style = self.STYLES[self.toast_type]
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(12)
        
        # Container with styling
        self.setStyleSheet(f"""
            ToastWidget {{
                background-color: {style['bg']};
                border-radius: 8px;
                border: 2px solid {style['border']};
            }}
        """)
        
        # Icon
        icon_label = QLabel(style['icon'])
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)
        
        # Message
        msg_label = QLabel(self.message)
        msg_label.setStyleSheet("""
            color: white;
            font-size: 13px;
            font-weight: 500;
            background: transparent;
        """)
        msg_label.setWordWrap(True)
        msg_label.setMaximumWidth(300)
        layout.addWidget(msg_label, 1)
        
        # Action button (Enterprise feature)
        if self.action_text:
            self.action_btn = QPushButton(self.action_text)
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.25);
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    border: 1px solid rgba(255,255,255,0.4);
                    border-radius: 4px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.4);
                }
                QPushButton:pressed {
                    background: rgba(255,255,255,0.5);
                }
            """)
            self.action_btn.clicked.connect(self._on_action_clicked)
            self.action_btn.setAccessibleName(f"Hành động: {self.action_text}")
            layout.addWidget(self.action_btn)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.2);
                border-radius: 12px;
            }
        """)
        close_btn.clicked.connect(self.dismiss)
        close_btn.setAccessibleName("Đóng thông báo")
        layout.addWidget(close_btn)
        
        self.setMinimumWidth(280)
        self.adjustSize()
        
    def _on_action_clicked(self):
        """Handle action button click."""
        ui_logger.info(f"Toast action clicked: '{self.action_text}'")
        self.action_clicked.emit()
        if self.action_callback:
            self.action_callback()
        self.dismiss()
        
    def _setup_animations(self):
        """Setup slide-in and fade animations."""
        # Opacity effect for fade
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Fade in
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Slide in animation (position based)
        self.slide_in = QPropertyAnimation(self, b"pos")
        self.slide_in.setDuration(300)
        self.slide_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(250)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self._on_fade_out_finished)
        
        # Auto-dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.dismiss)
        
    def set_slide_positions(self, start_x: int, target_x: int, y: int):
        """Set positions for slide-in animation."""
        self._start_x = start_x
        self._target_x = target_x
        self.slide_in.setStartValue(QPoint(start_x, y))
        self.slide_in.setEndValue(QPoint(target_x, y))
        
    def show_toast(self):
        """Show the toast with slide-in animation."""
        self.show()
        self.fade_in.start()
        self.slide_in.start()
        self.dismiss_timer.start(self.duration_ms)
        
    def dismiss(self):
        """Dismiss the toast with fade animation."""
        self.dismiss_timer.stop()
        self.fade_out.start()
        
    def _on_fade_out_finished(self):
        """Handle fade out completion."""
        self.hide()
        self.deleteLater()


class ToastManager:
    """Manages multiple toast notifications with Enterprise features.
    
    Usage:
        manager = ToastManager.get_instance()
        manager.show_success("Saved successfully!")
        manager.show_error("Failed to save!", action_text="Retry", action_callback=retry_fn)
    """
    
    _instance: Optional['ToastManager'] = None
    
    @classmethod
    def get_instance(cls) -> 'ToastManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = ToastManager()
        return cls._instance
    
    def __init__(self):
        self.active_toasts: List[ToastWidget] = []
        self.toast_spacing = 10
        self.margin_right = 20
        self.margin_bottom = 20
        
    def _get_parent_window(self) -> Optional[QWidget]:
        """Get the main application window."""
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if widget.isVisible() and widget.windowTitle():
                    return widget
        return None
        
    def _position_toast(self, toast: ToastWidget):
        """Position toast in bottom-right corner with slide-in setup."""
        parent = self._get_parent_window()
        if not parent:
            return
            
        # Calculate position
        parent_rect = parent.geometry()
        toast_height = toast.sizeHint().height()
        toast_width = toast.sizeHint().width()
        
        # Stack above existing toasts
        y_offset = self.margin_bottom
        for active_toast in self.active_toasts:
            if active_toast.isVisible() and active_toast != toast:
                y_offset += active_toast.height() + self.toast_spacing
        
        target_x = parent_rect.right() - toast_width - self.margin_right
        start_x = parent_rect.right() + 50  # Start off-screen
        y = parent_rect.bottom() - toast_height - y_offset
        
        # Setup slide animation
        toast.set_slide_positions(start_x, target_x, y)
        toast.move(start_x, y)
        
    def _on_toast_destroyed(self, toast: ToastWidget):
        """Handle toast destruction."""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            
    def show_toast(
        self, 
        message: str, 
        toast_type: ToastType = ToastType.INFO,
        duration_ms: int = 4000,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ):
        """Show a toast notification with optional action button.
        
        Args:
            message: Toast message
            toast_type: Type of toast (SUCCESS, ERROR, WARNING, INFO)
            duration_ms: Auto-dismiss duration in milliseconds
            action_text: Optional action button text (e.g., "Undo", "Retry")
            action_callback: Optional callback when action is clicked
        """
        toast = ToastWidget(
            message, 
            toast_type, 
            duration_ms,
            action_text=action_text,
            action_callback=action_callback
        )
        toast.destroyed.connect(lambda: self._on_toast_destroyed(toast))
        
        self.active_toasts.append(toast)
        self._position_toast(toast)
        toast.show_toast()
        
    def show_success(
        self, 
        message: str, 
        duration_ms: int = 4000,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ):
        """Show success toast with optional action."""
        self.show_toast(message, ToastType.SUCCESS, duration_ms, action_text, action_callback)
        
    def show_error(
        self, 
        message: str, 
        duration_ms: int = 5000,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ):
        """Show error toast with optional action (longer duration)."""
        ui_logger.error(f"Toast Error: {message}")  # Log errors for audit
        self.show_toast(message, ToastType.ERROR, duration_ms, action_text, action_callback)
        
    def show_warning(
        self, 
        message: str, 
        duration_ms: int = 4500,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ):
        """Show warning toast with optional action."""
        ui_logger.warning(f"Toast Warning: {message}")  # Log warnings
        self.show_toast(message, ToastType.WARNING, duration_ms, action_text, action_callback)
        
    def show_info(
        self, 
        message: str, 
        duration_ms: int = 4000,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ):
        """Show info toast with optional action."""
        self.show_toast(message, ToastType.INFO, duration_ms, action_text, action_callback)


# Convenience function for global access
def get_toast_manager() -> ToastManager:
    """Get the global toast manager instance."""
    return ToastManager.get_instance()
