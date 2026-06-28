"""Masonry grid layout for news cards.

Pinterest-style layout that optimizes vertical space usage.
Cards are arranged in columns with variable heights.
"""

from typing import List
from PySide6.QtWidgets import QLayout, QWidget, QLayoutItem, QWidgetItem
from PySide6.QtCore import Qt, QRect, QSize, QPoint


class MasonryLayout(QLayout):
    """Masonry (Pinterest-style) grid layout.
    
    Cards are placed in the column with the smallest height,
    creating a staggered, visually interesting layout.
    
    Usage:
        layout = MasonryLayout(columns=3, spacing=16)
        layout.addWidget(card1)
        layout.addWidget(card2)
        layout.addWidget(card3)
    """
    
    def __init__(self, parent=None, columns: int = 3, spacing: int = 16):
        super().__init__(parent)
        self._columns = columns
        self._spacing = spacing
        self._items: List[QLayoutItem] = []
        self._cached_geometry = None
        self._cached_size = None
    
    def addItem(self, item: QLayoutItem):
        """Add item to layout."""
        self._items.append(item)
        self._invalidate_cache()
    
    def addWidget(self, widget: QWidget):
        """Add widget to layout."""
        item = QWidgetItem(widget)
        self.addItem(item)
    
    def count(self) -> int:
        """Return number of items."""
        return len(self._items)
    
    def itemAt(self, index: int) -> QLayoutItem:
        """Return item at index."""
        if 0 <= index < len(self._items):
            return self._items[index]
        return None
    
    def takeAt(self, index: int) -> QLayoutItem:
        """Remove and return item at index."""
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self._invalidate_cache()
            return item
        return None
    
    def _invalidate_cache(self):
        """Invalidate cached calculations."""
        self._cached_geometry = None
        self._cached_size = None
    
    def setGeometry(self, rect: QRect):
        """Position all items within the given rect."""
        super().setGeometry(rect)
        
        if not self._items:
            return
        
        # Responsive columns based on width
        actual_columns = self._calculate_responsive_columns(rect.width())
        
        # Calculate column width
        available_width = rect.width() - (actual_columns - 1) * self._spacing
        col_width = available_width // actual_columns
        
        if col_width <= 0:
            return
        
        # Track height of each column
        col_heights = [0] * actual_columns
        
        # Position each item
        for item in self._items:
            widget = item.widget()
            if not widget:
                continue
            
            # Find the shortest column
            min_col = col_heights.index(min(col_heights))
            
            # Calculate position
            x = rect.x() + min_col * (col_width + self._spacing)
            y = rect.y() + col_heights[min_col]
            
            # Get item's preferred height
            hint = item.sizeHint()
            item_height = hint.height() if hint.height() > 0 else 200
            
            # Set item geometry
            item.setGeometry(QRect(x, y, col_width, item_height))
            
            # Update column height
            col_heights[min_col] += item_height + self._spacing
    
    def _calculate_responsive_columns(self, width: int) -> int:
        """Calculate optimal number of columns based on available width.
        
        Breakpoints:
        - < 600px: 1 column
        - 600-900px: 2 columns
        - 900-1200px: 3 columns
        - > 1200px: 4 columns (or user preference)
        """
        if width < 600:
            return 1
        elif width < 900:
            return 2
        elif width < 1200:
            return min(3, self._columns)
        else:
            return self._columns  # Use configured value
        
        # Track height of each column
        col_heights = [0] * self._columns
        
        # Position each item
        for item in self._items:
            widget = item.widget()
            if not widget:
                continue
            
            # Find the shortest column
            min_col = col_heights.index(min(col_heights))
            
            # Calculate position
            x = rect.x() + min_col * (col_width + self._spacing)
            y = rect.y() + col_heights[min_col]
            
            # Get item's preferred height
            hint = item.sizeHint()
            item_height = hint.height() if hint.height() > 0 else 200
            
            # Set item geometry
            item.setGeometry(QRect(x, y, col_width, item_height))
            
            # Update column height
            col_heights[min_col] += item_height + self._spacing
    
    def sizeHint(self) -> QSize:
        """Return preferred size."""
        return self.minimumSize()
    
    def minimumSize(self) -> QSize:
        """Return minimum size needed."""
        if not self._items:
            return QSize(0, 0)
        
        # Calculate based on current geometry
        width = self.geometry().width() or 400
        col_width = (width - (self._columns - 1) * self._spacing) // self._columns
        
        if col_width <= 0:
            col_width = 300
        
        # Track height of each column
        col_heights = [0] * self._columns
        
        for item in self._items:
            hint = item.sizeHint()
            item_height = hint.height() if hint.height() > 0 else 200
            
            # Find shortest column
            min_col = col_heights.index(min(col_heights))
            col_heights[min_col] += item_height + self._spacing
        
        max_height = max(col_heights) if col_heights else 0
        
        return QSize(width, max_height)
    
    def hasHeightForWidth(self) -> bool:
        """This layout has height-for-width dependency."""
        return True
    
    def heightForWidth(self, width: int) -> int:
        """Calculate height needed for given width."""
        if not self._items:
            return 0
        
        col_width = (width - (self._columns - 1) * self._spacing) // self._columns
        
        if col_width <= 0:
            return 0
        
        col_heights = [0] * self._columns
        
        for item in self._items:
            hint = item.sizeHint()
            item_height = hint.height() if hint.height() > 0 else 200
            
            min_col = col_heights.index(min(col_heights))
            col_heights[min_col] += item_height + self._spacing
        
        return max(col_heights) if col_heights else 0
    
    def expandingDirections(self):
        """Return expanding directions."""
        return Qt.Orientation(0)
    
    def setColumns(self, columns: int):
        """Set number of columns."""
        if columns > 0 and columns != self._columns:
            self._columns = columns
            self._invalidate_cache()
            self.update()
    
    def columns(self) -> int:
        """Get number of columns."""
        return self._columns
    
    def setSpacing(self, spacing: int):
        """Set spacing between items."""
        if spacing >= 0 and spacing != self._spacing:
            self._spacing = spacing
            self._invalidate_cache()
            self.update()
    
    def spacing(self) -> int:
        """Get spacing between items."""
        return self._spacing
    
    def clear(self):
        """Remove all items from layout."""
        while self._items:
            item = self._items.pop()
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._invalidate_cache()
