"""Custom Radar Chart Widget using QPainter."""
from typing import List, Dict, Union
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPolygonF
from PySide6.QtCore import Qt, QPointF, QSize, QRectF
from frontend.ui.styles.theme import ThemeColors

class RadarChart(QWidget):
    """
    Radar Chart (Spider Web Chart) for visualizing skills.
    
    Args:
        labels: List of labels (e.g., ["Part 1", "Part 2", ...])
        values: List of values 0-100 corresponding to labels
        title: Optional chart title
    """
    
    def __init__(self, labels: List[str] = None, values: List[float] = None, title: str = "", parent=None):
        super().__init__(parent)
        self.labels = labels or []
        self.values = values or []
        self.title = title
        
        # Style config
        self.line_color = QColor(ThemeColors.PRIMARY)
        self.fill_color = QColor(ThemeColors.PRIMARY)
        self.fill_color.setAlpha(100) # Semi-transparent
        self.grid_color = QColor(ThemeColors.BORDER)
        self.text_color = QColor(ThemeColors.TEXT_PRIMARY)
        
        self.setMinimumSize(300, 300)
        
    def set_data(self, labels: List[str], values: List[float]):
        """Update chart data."""
        self.labels = labels
        self.values = values
        self.update() # Trigger repaint

    def paintEvent(self, event):
        """Draw the radar chart."""
        if not self.labels or len(self.labels) < 3:
            return 
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        center = QPointF(rect.width() / 2, rect.height() / 2)
        
        # Radius (leave space for text)
        radius = min(rect.width(), rect.height()) / 2 * 0.75
        
        count = len(self.labels)
        angle_step = 2 * math.pi / count
        
        # 1. Draw Web/Grid (Background)
        painter.setPen(QPen(self.grid_color, 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        
        # Draw concentric polygons (20%, 40%, 60%, 80%, 100%)
        for i in range(1, 6):
            r = radius * (i / 5)
            poly = QPolygonF()
            for j in range(count):
                angle = j * angle_step - math.pi / 2 # Start from top
                x = center.x() + r * math.cos(angle)
                y = center.y() + r * math.sin(angle)
                poly.append(QPointF(x, y))
            painter.drawPolygon(poly)
            
        # Draw spokes
        painter.setPen(QPen(self.grid_color, 1))
        for j in range(count):
            angle = j * angle_step - math.pi / 2
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)
            painter.drawLine(center, QPointF(x, y))
            
            # Draw Labels
            label_radius = radius * 1.15
            lx = center.x() + label_radius * math.cos(angle)
            ly = center.y() + label_radius * math.sin(angle)
            
            # Adjust text rect to center on point
            text = self.labels[j]
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            w = metrics.horizontalAdvance(text)
            h = metrics.height()
            
            text_rect = QRectF(lx - w/2, ly - h/2, w, h)
            painter.setPen(self.text_color)
            painter.drawText(text_rect, Qt.AlignCenter, text)

        # 2. Draw Data Polygon
        if len(self.values) == count:
            data_poly = QPolygonF()
            for j in range(count):
                angle = j * angle_step - math.pi / 2
                val = max(0, min(100, self.values[j])) # Clamp 0-100
                r = radius * (val / 100)
                x = center.x() + r * math.cos(angle)
                y = center.y() + r * math.sin(angle)
                data_poly.append(QPointF(x, y))
                
            # Draw fill
            painter.setBrush(QBrush(self.fill_color))
            painter.setPen(QPen(self.line_color, 2))
            painter.drawPolygon(data_poly)
            
            # Draw Data Points
            painter.setBrush(QBrush(QColor("white")))
            painter.setPen(QPen(self.line_color, 2))
            for p in data_poly:
                painter.drawEllipse(p, 4, 4)

        # Draw Title
        if self.title:
            painter.setPen(self.text_color)
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRectF(0, 10, rect.width(), 30), Qt.AlignCenter, self.title)

