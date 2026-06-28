"""PathLine - Curved bezier path connecting grammar nodes on the Learning Map.

Styles:
- Locked: Dashed grey line
- Unlocked: Solid colored line
- Animated: Flowing dots effect (optional)
"""
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush


class PathLine(QGraphicsPathItem):
    """Curved path connecting two nodes."""
    
    def __init__(
        self,
        start_pos: QPointF,
        end_pos: QPointF,
        is_unlocked: bool = False,
        parent=None
    ):
        super().__init__(parent)
        
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.is_unlocked = is_unlocked
        
        # Create the bezier path
        self._create_path()
        
        # Apply styling
        self._apply_style()
        
        # Set z-order (below nodes)
        self.setZValue(-10)
    
    def _create_path(self):
        """Create a curved bezier path between start and end."""
        path = QPainterPath()
        path.moveTo(self.start_pos)
        
        # Calculate control points for smooth curve
        dx = self.end_pos.x() - self.start_pos.x()
        dy = self.end_pos.y() - self.start_pos.y()
        
        # Control point offset (curve intensity)
        offset = min(abs(dx), abs(dy)) * 0.5
        
        # Create S-curve or simple curve based on direction
        if abs(dx) > abs(dy):
            # Horizontal-ish path
            ctrl1 = QPointF(self.start_pos.x() + dx * 0.3, self.start_pos.y())
            ctrl2 = QPointF(self.end_pos.x() - dx * 0.3, self.end_pos.y())
        else:
            # Vertical-ish path
            ctrl1 = QPointF(self.start_pos.x(), self.start_pos.y() + dy * 0.3)
            ctrl2 = QPointF(self.end_pos.x(), self.end_pos.y() - dy * 0.3)
        
        path.cubicTo(ctrl1, ctrl2, self.end_pos)
        self.setPath(path)
    
    def _apply_style(self):
        """Apply visual style based on lock state."""
        if self.is_unlocked:
            # Solid colored line
            pen = QPen(QColor("#4ecdc4"), 3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        else:
            # Dashed grey line
            pen = QPen(QColor("#555555"), 2, Qt.PenStyle.DashLine)
            pen.setDashPattern([4, 4])
        
        self.setPen(pen)
        self.setBrush(Qt.BrushStyle.NoBrush)
    
    def set_unlocked(self, unlocked: bool):
        """Update locked/unlocked state."""
        self.is_unlocked = unlocked
        self._apply_style()
    
    def update_positions(self, start: QPointF, end: QPointF):
        """Update path when nodes move."""
        self.start_pos = start
        self.end_pos = end
        self._create_path()


class NodeConnector:
    """Helper class to manage path lines between nodes."""
    
    def __init__(self, scene):
        self.scene = scene
        self.paths: list[PathLine] = []
    
    def connect_nodes(self, from_node, to_node, is_unlocked: bool = False) -> PathLine:
        """Create a path connecting two nodes."""
        # Get center positions
        start = from_node.scenePos()
        end = to_node.scenePos()
        
        # Create path
        path = PathLine(start, end, is_unlocked)
        self.scene.addItem(path)
        self.paths.append(path)
        
        return path
    
    def clear_all(self):
        """Remove all paths from scene."""
        for path in self.paths:
            self.scene.removeItem(path)
        self.paths.clear()
    
    def update_path_status(self, from_id: int, to_id: int, unlocked: bool):
        """Update a specific path's unlock status."""
        # This would need node ID tracking - simplified for now
        pass
