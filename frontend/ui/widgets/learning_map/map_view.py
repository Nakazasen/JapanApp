"""MapView - QGraphicsView with zoom/pan support for the Learning Map.

Features:
- Scroll-to-zoom with smooth animation
- Drag-to-pan navigation
- Fit-to-region on double-click
- Zoom limits (50% - 200%)
"""
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter


class MapView(QGraphicsView):
    """Custom QGraphicsView with zoom/pan support."""
    
    # Signals
    zoom_changed = Signal(float)  # Emits new zoom level (1.0 = 100%)
    region_clicked = Signal(str)  # Emits region id when double-clicking
    
    # Zoom limits
    MIN_ZOOM = 0.5   # 50%
    MAX_ZOOM = 2.0   # 200%
    ZOOM_STEP = 0.1  # 10% per scroll step
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Current zoom level (1.0 = 100%)
        self._zoom_level = 1.0
        
        # Animation for smooth zoom
        self._zoom_animation = QPropertyAnimation(self, b"zoom_level")
        self._zoom_animation.setDuration(150)
        self._zoom_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Setup view
        self._setup_view()
    
    def _setup_view(self):
        """Configure the graphics view."""
        # Enable antialiasing for smooth graphics
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        
        # Enable click-to-select (NoDrag mode allows clicks to register)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        # Optimize performance
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        
        # Hide scrollbars for clean look
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set background
        self.setStyleSheet("""
            QGraphicsView {
                border: none;
                background-color: #0f0f1a;
            }
        """)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
    
    # ============ Zoom Property ============
    
    def get_zoom_level(self) -> float:
        return self._zoom_level
    
    def set_zoom_level(self, value: float):
        """Set zoom level with bounds checking."""
        # Clamp to limits
        value = max(self.MIN_ZOOM, min(self.MAX_ZOOM, value))
        
        if value != self._zoom_level:
            # Calculate scale factor
            factor = value / self._zoom_level
            self._zoom_level = value
            
            # Apply transform
            self.scale(factor, factor)
            self.zoom_changed.emit(value)
    
    # Property for animation
    zoom_level = Property(float, get_zoom_level, set_zoom_level)
    
    # ============ Zoom Methods ============
    
    def zoom_to(self, level: float, animated: bool = True):
        """Zoom to specific level.
        
        Args:
            level: Target zoom level (1.0 = 100%)
            animated: Whether to animate the transition
        """
        level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, level))
        
        if animated:
            self._zoom_animation.stop()
            self._zoom_animation.setStartValue(self._zoom_level)
            self._zoom_animation.setEndValue(level)
            self._zoom_animation.start()
        else:
            self.set_zoom_level(level)
    
    def zoom_in(self, animated: bool = True):
        """Zoom in by one step."""
        self.zoom_to(self._zoom_level + self.ZOOM_STEP, animated)
    
    def zoom_out(self, animated: bool = True):
        """Zoom out by one step."""
        self.zoom_to(self._zoom_level - self.ZOOM_STEP, animated)
    
    def zoom_reset(self, animated: bool = True):
        """Reset zoom to 100%."""
        self.zoom_to(1.0, animated)
    
    def fit_to_region(self, rect, animated: bool = True):
        """Fit view to show a specific region rectangle.
        
        Args:
            rect: QRectF of the region to fit
            animated: Whether to animate the transition
        """
        if rect.isValid():
            # Calculate required zoom to fit
            viewport_rect = self.viewport().rect()
            h_ratio = viewport_rect.width() / rect.width()
            v_ratio = viewport_rect.height() / rect.height()
            zoom = min(h_ratio, v_ratio) * 0.9  # 90% to add margin
            
            # Center on region
            self.centerOn(rect.center())
            self.zoom_to(zoom, animated)
    
    # ============ Event Handlers ============
    
    def wheelEvent(self, event):
        """Handle scroll-to-zoom."""
        # Get zoom direction
        delta = event.angleDelta().y()
        
        if delta > 0:
            # Zoom in
            target_zoom = self._zoom_level + self.ZOOM_STEP
        else:
            # Zoom out
            target_zoom = self._zoom_level - self.ZOOM_STEP
        
        # Get cursor position for zoom centering
        cursor_pos = event.position().toPoint()
        scene_pos = self.mapToScene(cursor_pos)
        
        # Apply zoom
        self.zoom_to(target_zoom, animated=False)
        
        # Re-center on cursor position
        new_pos = self.mapFromScene(scene_pos)
        delta_pos = cursor_pos - new_pos
        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() - delta_pos.x()
        )
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() - delta_pos.y()
        )
        
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to fit region or reset zoom."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get clicked item
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, self.transform())
            
            if item:
                # Check if it's a region background
                region_id = item.data(0)  # Stored in data(0)
                if region_id:
                    self.region_clicked.emit(region_id)
                    return
            
            # Default: reset zoom
            self.zoom_reset()
        
        super().mouseDoubleClickEvent(event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for navigation."""
        key = event.key()
        
        # Zoom shortcuts
        if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            self.zoom_in()
        elif key == Qt.Key.Key_Minus:
            self.zoom_out()
        elif key == Qt.Key.Key_0:
            self.zoom_reset()
        # Region shortcuts (1-5)
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_5:
            region_index = key - Qt.Key.Key_1
            regions = ["a1", "a2", "b1", "b2", "c1"]
            if region_index < len(regions):
                self.region_clicked.emit(regions[region_index])
        else:
            super().keyPressEvent(event)
