"""
Animation utilities for the application.
Provides a centralized service for consistent animations (fade, slide, shake, flip).
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect, QParallelAnimationGroup, QSequentialAnimationGroup, QAbstractAnimation
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QColor

class AnimationService:
    """Centralized service for widget animations."""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300, easing=QEasingCurve.Type.OutCubic):
        """Fade in a widget from opacity 0 to 1."""
        # Ensure widget has an opacity effect
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        # Create animation
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(easing)
        
        # Keep reference to avoid garbage collection if needed, 
        # though usually parent ownership is enough. 
        # For simple fire-and-forget, we attach it to the widget.
        widget._fade_anim = anim
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    @staticmethod
    def slide_in(widget: QWidget, start_pos: QPoint, end_pos: QPoint, duration: int = 400, easing=QEasingCurve.Type.OutBack):
        """Slide a widget from start_pos to end_pos."""
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(easing)
        
        widget._slide_anim = anim
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    @staticmethod
    def shake(widget: QWidget, duration: int = 500):
        """Shake a widget (e.g. for error feedback)."""
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setLoopCount(1)
        
        current_pos = widget.pos()
        x = current_pos.x()
        y = current_pos.y()
        
        # Keyframes for shake
        anim.setKeyValueAt(0, QPoint(x, y))
        anim.setKeyValueAt(0.1, QPoint(x + 5, y))
        anim.setKeyValueAt(0.2, QPoint(x - 5, y))
        anim.setKeyValueAt(0.3, QPoint(x + 5, y))
        anim.setKeyValueAt(0.4, QPoint(x - 5, y))
        anim.setKeyValueAt(0.5, QPoint(x + 5, y))
        anim.setKeyValueAt(0.6, QPoint(x - 5, y))
        anim.setKeyValueAt(1, QPoint(x, y))
        
        widget._shake_anim = anim
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    @staticmethod
    def flip_stacked_widget(stacked_widget, duration=300, easing=QEasingCurve.Type.InOutQuad):
        """
        Simulate a 3D flip by shrinking width to 0, switching page, then expanding.
        
        Args:
            stacked_widget: QStackedWidget instance.
            duration: Total duration (split between shrink and expand).
            easing: Easing curve.
        """
        parent = stacked_widget.parentWidget()
        if not parent:
            # If no parent, we can't easily animate geometry constraint in layout context,
            # but we can try animating the stacked_widget itself if it has fixed size.
            parent = stacked_widget
            
        # We'll rely on a temporary property or use maximumWidth constraint
        # Current width
        start_width = stacked_widget.width()
        half_duration = duration // 2
        
        # Phase 1: Shrink
        anim1 = QPropertyAnimation(stacked_widget, b"maximumWidth")
        anim1.setDuration(half_duration)
        anim1.setStartValue(start_width)
        anim1.setEndValue(0)
        anim1.setEasingCurve(easing)
        
        # Phase 2: Expand
        anim2 = QPropertyAnimation(stacked_widget, b"maximumWidth")
        anim2.setDuration(half_duration)
        anim2.setStartValue(0)
        anim2.setEndValue(start_width)
        anim2.setEasingCurve(easing)
        
        # Sequence
        group = QSequentialAnimationGroup(stacked_widget)
        group.addAnimation(anim1)
        group.addAnimation(anim2)
        
        def on_mid_flip():
            # Switch page when width is 0
            current = stacked_widget.currentIndex()
            next_idx = (current + 1) % stacked_widget.count()
            stacked_widget.setCurrentIndex(next_idx)
            
        def on_finished():
            # Restore maximumWidth to unlimited/original to prevent layout locking
            stacked_widget.setMaximumWidth(16777215) # QWIDGETSIZE_MAX
            
        anim1.finished.connect(on_mid_flip)
        group.finished.connect(on_finished)
        
        # Prevent GC
        stacked_widget._flip_anim = group
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        return group

    @staticmethod
    def animate_width(widget: QWidget, start_width: int, end_width: int, duration: int = 300, easing=QEasingCurve.Type.InOutQuad):
        """Animate widget width."""
        anim = QPropertyAnimation(widget, b"minimumWidth")
        anim.setDuration(duration)
        anim.setStartValue(start_width)
        anim.setEndValue(end_width)
        anim.setEasingCurve(easing)
        
        # Also animate maximum width to force strict sizing if needed
        anim_max = QPropertyAnimation(widget, b"maximumWidth")
        anim_max.setDuration(duration)
        anim_max.setStartValue(start_width)
        anim_max.setEndValue(end_width)
        anim_max.setEasingCurve(easing)
        
        group = QParallelAnimationGroup(widget)
        group.addAnimation(anim)
        group.addAnimation(anim_max)
        
        widget._width_anim = group
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        return group
