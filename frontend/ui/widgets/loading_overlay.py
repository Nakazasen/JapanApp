"""Loading Overlay Widget - Enterprise Edition.

Provides loading feedback for async operations with:
- Spinner overlay
- Skeleton loading screens
- Timeout logging for audit trail
"""
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen, QConicalGradient, QLinearGradient
from typing import Optional, List
import logging

# Setup logger for UI events (Enterprise audit trail)
ui_logger = logging.getLogger("ui.loading")
ui_logger.setLevel(logging.INFO)


class SpinnerWidget(QWidget):
    """Animated spinner widget."""
    
    def __init__(self, size: int = 50, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._line_width = max(3, size // 12)
        self._color = QColor("#3498db")
        
        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(16)  # ~60fps
        
    def set_color(self, color: QColor):
        """Set spinner color."""
        self._color = color
        self.update()
        
    def start(self):
        """Start spinning animation."""
        self._timer.start()
        
    def stop(self):
        """Stop spinning animation."""
        self._timer.stop()
        
    def _rotate(self):
        """Rotate the spinner."""
        self._angle = (self._angle + 6) % 360
        self.update()
        
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions
        size = min(self.width(), self.height())
        rect_size = size - self._line_width * 2
        
        # Create gradient for smooth spinning effect
        gradient = QConicalGradient(size / 2, size / 2, -self._angle)
        gradient.setColorAt(0, self._color)
        gradient.setColorAt(0.7, QColor(self._color.red(), self._color.green(), 
                                         self._color.blue(), 50))
        gradient.setColorAt(1, Qt.transparent)
        
        # Draw arc
        pen = QPen()
        pen.setWidth(self._line_width)
        pen.setBrush(gradient)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        painter.drawArc(
            self._line_width, 
            self._line_width,
            rect_size, 
            rect_size,
            0 * 16, 
            270 * 16  # Draw 270 degrees
        )


class SkeletonWidget(QWidget):
    """Skeleton loading placeholder with shimmer animation.
    
    Enterprise Feature: Shows content structure while loading for better UX.
    
    Usage:
        skeleton = SkeletonWidget(width=200, height=120)
        skeleton.start_shimmer()
        # ... data loads ...
        skeleton.stop_shimmer()
        skeleton.hide()
    """
    
    def __init__(
        self, 
        width: int = 200, 
        height: int = 100,
        border_radius: int = 8,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._border_radius = border_radius
        self._shimmer_pos = -width  # Start off-screen left
        self._base_color = QColor("#2d2d3a")
        self._shimmer_color = QColor("#3d3d4a")
        
        # Shimmer animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_shimmer)
        self._timer.setInterval(16)  # ~60fps
        
    def start_shimmer(self):
        """Start shimmer animation."""
        self._timer.start()
        
    def stop_shimmer(self):
        """Stop shimmer animation."""
        self._timer.stop()
        
    def _animate_shimmer(self):
        """Move shimmer across the widget."""
        self._shimmer_pos += 4
        if self._shimmer_pos > self.width() * 2:
            self._shimmer_pos = -self.width()
        self.update()
        
    def paintEvent(self, event):
        """Paint skeleton with shimmer effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Base rounded rectangle
        painter.setBrush(self._base_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        
        # Shimmer gradient overlay
        shimmer_width = self.width() // 2
        gradient = QLinearGradient(self._shimmer_pos, 0, self._shimmer_pos + shimmer_width, 0)
        gradient.setColorAt(0, Qt.transparent)
        gradient.setColorAt(0.5, QColor(255, 255, 255, 30))
        gradient.setColorAt(1, Qt.transparent)
        
        painter.setBrush(gradient)
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)


class SkeletonStatCard(QFrame):
    """Skeleton placeholder for StatCard on Dashboard.
    
    Mimics the layout of StatCard while data is loading.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(210, 130)
        self.setStyleSheet("""
            SkeletonStatCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2d2d3a, stop:1 #24242e);
                border-radius: 16px;
                border: 1px solid #404050;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header skeleton (icon + title)
        header = QHBoxLayout()
        self.icon_skeleton = SkeletonWidget(30, 30, 6)
        header.addWidget(self.icon_skeleton)
        self.title_skeleton = SkeletonWidget(80, 14, 4)
        header.addWidget(self.title_skeleton)
        header.addStretch()
        layout.addLayout(header)
        
        # Value skeleton (big number)
        self.value_skeleton = SkeletonWidget(100, 36, 6)
        layout.addWidget(self.value_skeleton)
        
        layout.addStretch()
        
    def start_shimmer(self):
        """Start all skeletons shimmer."""
        self.icon_skeleton.start_shimmer()
        self.title_skeleton.start_shimmer()
        self.value_skeleton.start_shimmer()
        
    def stop_shimmer(self):
        """Stop all skeletons shimmer."""
        self.icon_skeleton.stop_shimmer()
        self.title_skeleton.stop_shimmer()
        self.value_skeleton.stop_shimmer()


class LoadingOverlay(QWidget):
    """Semi-transparent loading overlay with spinner.
    
    Usage:
        overlay = LoadingOverlay(parent_widget, "Loading...")
        overlay.show_overlay()
        # ... do work ...
        overlay.hide_overlay()
    """
    
    def __init__(
        self, 
        parent: QWidget,
        message: str = "Đang tải...",
        spinner_color: Optional[QColor] = None,
        timeout_ms: Optional[int] = 30000  # 30 second timeout for logging
    ):
        super().__init__(parent)
        self.message = message
        self.spinner_color = spinner_color or QColor("#3498db")
        self.timeout_ms = timeout_ms
        self._start_time = None
        
        self._setup_ui()
        self._setup_animations()
        self._setup_timeout_logging()
        self.hide()
        
    def _setup_ui(self):
        """Setup overlay UI."""
        self.setStyleSheet("""
            LoadingOverlay {
                background-color: rgba(0, 0, 0, 0.6);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Container for spinner and message
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 0.95);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(16)
        
        # Spinner
        self.spinner = SpinnerWidget(50)
        self.spinner.set_color(self.spinner_color)
        container_layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        
        # Message label
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: 500;
            background: transparent;
        """)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setAccessibleName(self.message)
        container_layout.addWidget(self.message_label)
        
        container.setFixedSize(200, 140)
        layout.addWidget(container)
        
    def _setup_animations(self):
        """Setup fade animations."""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Fade in
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(150)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(150)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self._on_fade_out_finished)
        
    def _setup_timeout_logging(self):
        """Setup timeout logging for long-running operations."""
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_timeout)
        
    def _on_timeout(self):
        """Log when loading takes too long (Enterprise audit)."""
        ui_logger.warning(
            f"Loading timeout: '{self.message}' exceeded {self.timeout_ms/1000:.1f}s"
        )
        
    def set_message(self, message: str):
        """Update loading message."""
        self.message = message
        self.message_label.setText(message)
        self.message_label.setAccessibleName(message)
        
    def show_overlay(self):
        """Show the loading overlay."""
        import time
        self._start_time = time.time()
        
        if self.parent():
            self.resize(self.parent().size())
        self.raise_()
        self.show()
        self.spinner.start()
        self.fade_in.start()
        
        # Start timeout timer
        if self.timeout_ms:
            self.timeout_timer.start(self.timeout_ms)
        
    def hide_overlay(self):
        """Hide the loading overlay."""
        import time
        
        self.timeout_timer.stop()
        
        # Log duration for audit
        if self._start_time:
            duration = time.time() - self._start_time
            if duration > 3:  # Log if > 3 seconds
                ui_logger.info(f"Loading completed: '{self.message}' took {duration:.2f}s")
        
        self.fade_out.start()
        
    def _on_fade_out_finished(self):
        """Handle fade out completion."""
        self.spinner.stop()
        self.hide()
        
    def resizeEvent(self, event):
        """Handle parent resize."""
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)
        
    def __enter__(self):
        self.show_overlay()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.hide_overlay()
        return False


class LoadingOverlayManager:
    """Helper class to manage loading overlays for widgets."""
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.overlay: Optional[LoadingOverlay] = None
        
    def show(self, message: str = "Đang tải..."):
        """Show loading overlay."""
        if self.overlay is None:
            self.overlay = LoadingOverlay(self.parent, message)
        else:
            self.overlay.set_message(message)
        self.overlay.show_overlay()
        
    def hide(self):
        """Hide loading overlay."""
        if self.overlay:
            self.overlay.hide_overlay()
            
    def is_visible(self) -> bool:
        """Check if overlay is visible."""
        return self.overlay is not None and self.overlay.isVisible()


class SkeletonManager:
    """Manages skeleton placeholders for a widget.
    
    Enterprise Feature: Replace spinners with skeleton screens.
    
    Usage:
        # Create skeletons matching your layout
        manager = SkeletonManager(parent)
        manager.add_stat_card_skeleton(x=0, y=0)
        manager.add_stat_card_skeleton(x=220, y=0)
        manager.show()
        # ... data loads ...
        manager.hide()
    """
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.skeletons: List[QWidget] = []
        
    def add_skeleton(self, skeleton: QWidget, x: int = 0, y: int = 0):
        """Add a skeleton at specified position."""
        skeleton.setParent(self.parent)
        skeleton.move(x, y)
        self.skeletons.append(skeleton)
        
    def add_stat_card_skeleton(self, x: int = 0, y: int = 0):
        """Add a StatCard skeleton."""
        skeleton = SkeletonStatCard()
        self.add_skeleton(skeleton, x, y)
        return skeleton
        
    def show(self):
        """Show all skeletons with shimmer."""
        for skeleton in self.skeletons:
            skeleton.show()
            if hasattr(skeleton, 'start_shimmer'):
                skeleton.start_shimmer()
                
    def hide(self):
        """Hide all skeletons."""
        for skeleton in self.skeletons:
            if hasattr(skeleton, 'stop_shimmer'):
                skeleton.stop_shimmer()
            skeleton.hide()
            
    def clear(self):
        """Remove all skeletons."""
        for skeleton in self.skeletons:
            skeleton.deleteLater()
        self.skeletons.clear()
