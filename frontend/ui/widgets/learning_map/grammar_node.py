"""GrammarNode - Interactive node representing a grammar item on the Learning Map.

Visual States:
- LOCKED: Dark/grey, lock icon, not clickable
- AVAILABLE: Glowing border, ready to learn
- LEARNING: Pulsing animation, in progress
- MASTERED: Gold star badge, completed
"""
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsDropShadowEffect, QStyleOptionGraphicsItem, QWidget,
    QToolTip
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QRadialGradient, QLinearGradient
)

from frontend.models.learning_progress import MapStatus, LearningProgress


# Visual configuration for each state
NODE_STYLES = {
    MapStatus.LOCKED: {
        "bg_color": "#2d2d2d",
        "border_color": "#555555",
        "text_color": "#888888",
        "icon": "🔒",
        "glow": False,
    },
    MapStatus.AVAILABLE: {
        "bg_color": "#3a506b",
        "border_color": "#5bc0be",
        "text_color": "#e0e0e0",
        "icon": "📘",
        "glow": True,
    },
    MapStatus.LEARNING: {
        "bg_color": "#0b132b",
        "border_color": "#6fffe9",
        "text_color": "#ffffff",
        "icon": "📖",
        "glow": True,
    },
    MapStatus.MASTERED: {
        "bg_color": "#1a535c",
        "border_color": "#ffd166",
        "text_color": "#ffffff",
        "icon": "⭐",
        "glow": True,
    },
}


class NodeSignals(QObject):
    """Signals for GrammarNode (QGraphicsItem can't have signals directly)."""
    clicked = Signal(int)  # grammar_id
    hovered = Signal(int, bool)  # grammar_id, is_hovered


class GrammarNode(QGraphicsItem):
    """Interactive node representing a grammar item on the map."""
    
    # Node dimensions
    RADIUS = 35
    BOSS_RADIUS = 50
    BORDER_WIDTH = 3
    
    def __init__(
        self,
        grammar_id: int,
        title: str,
        status: MapStatus = MapStatus.LOCKED,
        is_boss: bool = False,
        progress_percent: float = 0.0,
        parent=None
    ):
        super().__init__(parent)
        
        # Data
        self.grammar_id = grammar_id
        self.title = title
        self.status = status
        self.is_boss = is_boss
        self.progress_percent = progress_percent
        self.description = ""
        
        # Visual
        self._hovered = False
        self._pulse_phase = 0.0
        self._pulse_timer = None
        
        # Signals
        self.signals = NodeSignals()
        
        # Setup
        self._setup_item()
        
        # Pulse animation disabled for performance (too many nodes)
        # if status == MapStatus.LEARNING:
        #     self._start_pulse()
    
    def _setup_item(self):
        """Configure the graphics item."""
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.status != MapStatus.LOCKED 
                       else Qt.CursorShape.ForbiddenCursor)
        
        # Store id for click detection
        self.setData(0, f"node_{self.grammar_id}")
    
    @property
    def radius(self) -> float:
        """Get node radius based on type."""
        return self.BOSS_RADIUS if self.is_boss else self.RADIUS
    
    @property
    def style(self) -> dict:
        """Get current visual style."""
        return NODE_STYLES.get(self.status, NODE_STYLES[MapStatus.LOCKED])
    
    # ============ Qt Graphics Item Methods ============
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle."""
        r = self.radius + 10  # Extra padding for glow
        return QRectF(-r, -r, r * 2, r * 2)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the node."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        style = self.style
        r = self.radius
        
        # Draw glow effect for non-locked nodes
        if style["glow"] or self._hovered:
            self._draw_glow(painter, r, style)
        
        # Draw progress ring (behind main circle)
        if self.progress_percent > 0:
            self._draw_progress_ring(painter, r)
        
        # Draw main circle background
        self._draw_background(painter, r, style)
        
        # Draw border
        self._draw_border(painter, r, style)
        
        # Draw icon and text
        self._draw_content(painter, r, style)
        
        # Draw boss crown
        if self.is_boss:
            self._draw_boss_badge(painter, r)
    
    def _draw_glow(self, painter: QPainter, r: float, style: dict):
        """Draw glow effect around node."""
        glow_color = QColor(style["border_color"])
        glow_color.setAlpha(60 if not self._hovered else 100)
        
        # Pulsing effect for learning nodes
        glow_radius = r + 8
        if self.status == MapStatus.LEARNING:
            glow_radius += 4 * abs(self._pulse_phase)
        
        gradient = QRadialGradient(0, 0, glow_radius)
        gradient.setColorAt(0.6, glow_color)
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), glow_radius, glow_radius)
    
    def _draw_progress_ring(self, painter: QPainter, r: float):
        """Draw circular progress indicator."""
        ring_width = 4
        ring_radius = r + 2
        
        # Background ring
        painter.setPen(QPen(QColor("#333333"), ring_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0, 0), ring_radius, ring_radius)
        
        # Progress arc
        progress_color = QColor("#4ecdc4") if self.progress_percent < 100 else QColor("#ffd166")
        painter.setPen(QPen(progress_color, ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        
        # Draw arc (angles in 1/16th degrees, starting from top)
        start_angle = 90 * 16  # 12 o'clock
        span_angle = int(-self.progress_percent / 100 * 360 * 16)
        
        rect = QRectF(-ring_radius, -ring_radius, ring_radius * 2, ring_radius * 2)
        painter.drawArc(rect, start_angle, span_angle)
    
    def _draw_background(self, painter: QPainter, r: float, style: dict):
        """Draw node background circle."""
        gradient = QRadialGradient(0, -r * 0.3, r * 1.5)
        
        bg_color = QColor(style["bg_color"])
        lighter = bg_color.lighter(130)
        
        gradient.setColorAt(0, lighter)
        gradient.setColorAt(1, bg_color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), r, r)
    
    def _draw_border(self, painter: QPainter, r: float, style: dict):
        """Draw node border."""
        border_color = QColor(style["border_color"])
        
        # Thicker border when hovered
        width = self.BORDER_WIDTH + (2 if self._hovered else 0)
        
        painter.setPen(QPen(border_color, width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0, 0), r - width / 2, r - width / 2)
    
    def _draw_content(self, painter: QPainter, r: float, style: dict):
        """Draw icon and title text."""
        # Icon - using Segoe UI Emoji or fallback
        icon_font = QFont("Segoe UI Emoji", int(r * 0.6))
        painter.setFont(icon_font)
        painter.setPen(QColor(style["text_color"]))
        
        icon_rect = QRectF(-r, -r * 0.5, r * 2, r)
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, style["icon"])
        
        # Title (below icon, truncated if too long)
        title_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(title_font)
        
        display_title = self.title[:8] + "…" if len(self.title) > 8 else self.title
        title_rect = QRectF(-r - 5, r * 0.2, r * 2 + 10, r * 0.6)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, display_title)
    
    def _draw_boss_badge(self, painter: QPainter, r: float):
        """Draw crown badge for boss nodes."""
        # Crown at top
        crown_font = QFont("", 16)
        painter.setFont(crown_font)
        painter.setPen(QColor("#ffd166"))
        
        crown_rect = QRectF(-15, -r - 20, 30, 20)
        painter.drawText(crown_rect, Qt.AlignmentFlag.AlignCenter, "👑")
    
    # ============ Animation ============
    
    def _start_pulse(self):
        """Start pulsing animation for learning nodes."""
        if self._pulse_timer is None:
            self._pulse_timer = QTimer()
            self._pulse_timer.timeout.connect(self._update_pulse)
            self._pulse_timer.start(50)  # 20 fps
    
    def _stop_pulse(self):
        """Stop pulsing animation."""
        if self._pulse_timer:
            self._pulse_timer.stop()
            self._pulse_timer = None
    
    def _update_pulse(self):
        """Update pulse animation phase."""
        import math
        self._pulse_phase = math.sin(self._pulse_phase * 2 * math.pi + 0.1)
        if self.scene():
            self.update()
    
    # ============ Events ============
    
    def hoverEnterEvent(self, event):
        """Handle mouse hover enter."""
        self._hovered = True
        self.signals.hovered.emit(self.grammar_id, True)
        self.update()
        
        # Show tooltip
        tooltip_text = f"<b>{self.title}</b><br>"
        tooltip_text += f"Status: {self.status.value.title()}<br>"
        if self.progress_percent > 0:
            tooltip_text += f"Progress: {self.progress_percent:.0f}%"
        if self.description:
            tooltip_text += f"<br><i>{self.description}</i>"
        
        self.setToolTip(tooltip_text)
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave."""
        self._hovered = False
        self.signals.hovered.emit(self.grammar_id, False)
        self.update()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.status != MapStatus.LOCKED:
                print(f"[GrammarNode] Clicked node ID: {self.grammar_id}, status: {self.status}")
                self.signals.clicked.emit(self.grammar_id)
        super().mousePressEvent(event)
    
    # ============ State Updates ============
    
    def set_status(self, status: MapStatus):
        """Update node status and visual."""
        self.status = status
        
        # Update cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor if status != MapStatus.LOCKED 
                       else Qt.CursorShape.ForbiddenCursor)
        
        # Pulse animation disabled for performance
        # if status == MapStatus.LEARNING:
        #     self._start_pulse()
        # else:
        #     self._stop_pulse()
        
        self.update()
    
    def set_progress(self, percent: float):
        """Update progress percentage."""
        self.progress_percent = max(0, min(100, percent))
        self.update()
    
    @classmethod
    def from_progress(cls, progress: LearningProgress, title: str) -> "GrammarNode":
        """Create node from LearningProgress data."""
        node = cls(
            grammar_id=progress.grammar_id,
            title=title,
            status=MapStatus(progress.map_status),
            is_boss=progress.is_boss_node,
            progress_percent=(progress.correct_count / max(progress.attempts, 1) * 100) 
                             if progress.attempts > 0 else 0,
        )
        node.setPos(progress.position_x, progress.position_y)
        return node
