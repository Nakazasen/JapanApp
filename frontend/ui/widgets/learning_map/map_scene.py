"""MapScene - QGraphicsScene for the Learning Map.

Contains:
- Region backgrounds with Fantasy theme gradients
- Grammar nodes from database
- Region labels and progress indicators
- Path lines connecting nodes
"""
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, Signal, QObject
from PySide6.QtGui import (
    QBrush, QPen, QColor, QLinearGradient, 
    QFont, QPainterPath
)

from frontend.models.learning_progress import MapRegion, MapStatus, REGION_CONFIG, get_region_from_level


class SceneSignals(QObject):
    """Signals for MapScene."""
    node_clicked = Signal(int)  # grammar_id


class MapScene(QGraphicsScene):
    """Graphics scene containing the Learning Map."""
    
    # Region layout - horizontal arrangement
    REGION_WIDTH = 800
    REGION_HEIGHT = 600
    REGION_SPACING = 50
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Calculate total scene size
        total_width = (self.REGION_WIDTH + self.REGION_SPACING) * 5 - self.REGION_SPACING
        self.setSceneRect(0, 0, total_width, self.REGION_HEIGHT)
        
        # Store region bounds
        self._region_bounds: dict[MapRegion, QRectF] = {}
        
        # Store region stats for labels
        self._region_stats: dict[MapRegion, dict] = {}
        
        # Store grammar nodes by ID
        self._nodes: dict[int, "GrammarNode"] = {}
        
        # Store path lines
        self._paths: list = []
        
        # Signals
        self.signals = SceneSignals()
        
        # Create scene elements
        self._create_regions()
    
    def _create_regions(self):
        """Create region backgrounds with Fantasy theme."""
        for i, region in enumerate(MapRegion):
            x = i * (self.REGION_WIDTH + self.REGION_SPACING)
            rect = QRectF(x, 0, self.REGION_WIDTH, self.REGION_HEIGHT)
            self._region_bounds[region] = rect
            
            # Create region background
            self._create_region_background(region, rect)
            
            # Create region label
            self._create_region_label(region, rect)
    
    def _create_region_background(self, region: MapRegion, rect: QRectF):
        """Create gradient background for a region."""
        config = REGION_CONFIG[region]
        
        # Create gradient from top to bottom
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        
        primary = QColor(config["color_primary"])
        secondary = QColor(config["color_secondary"])
        
        # Make colors slightly transparent for depth
        primary.setAlpha(200)
        secondary.setAlpha(150)
        
        gradient.setColorAt(0, primary)
        gradient.setColorAt(1, secondary)
        
        # Create rectangle item
        bg_item = QGraphicsRectItem(rect)
        bg_item.setBrush(QBrush(gradient))
        bg_item.setPen(QPen(Qt.PenStyle.NoPen))
        bg_item.setZValue(-100)  # Behind everything
        bg_item.setData(0, region.value)  # Store region id for click detection
        
        self.addItem(bg_item)
        
        # Add decorative border between regions
        if region != MapRegion.C1:  # Not the last region
            border_x = rect.right() + self.REGION_SPACING / 2
            border = self.addLine(
                border_x, 20, border_x, self.REGION_HEIGHT - 20,
                QPen(QColor(255, 255, 255, 30), 2, Qt.PenStyle.DashLine)
            )
            border.setZValue(-50)
    
    def _create_region_label(self, region: MapRegion, rect: QRectF):
        """Create floating label with region name and progress."""
        config = REGION_CONFIG[region]
        
        # Create label text
        label = QGraphicsTextItem()
        label.setHtml(f"""
            <div style="text-align: center;">
                <span style="font-size: 32px;">{config['icon']}</span><br/>
                <span style="font-size: 18px; font-weight: bold; color: white;">
                    {config['name']}
                </span><br/>
                <span style="font-size: 12px; color: rgba(255,255,255,0.7);">
                    0/0 ✅
                </span>
            </div>
        """)
        
        label.setDefaultTextColor(Qt.GlobalColor.white)
        label.setPos(rect.center().x() - 60, rect.top() + 20)
        label.setZValue(50)  # Above background
        label.setData(0, f"label_{region.value}")
        
        self.addItem(label)
    
    def get_region_rect(self, region: MapRegion) -> QRectF:
        """Get bounding rectangle for a region."""
        return self._region_bounds.get(region, QRectF())
    
    def update_region_stats(self, stats_list: list[dict]):
        """Update region labels with progress stats.
        
        Args:
            stats_list: List of stats dicts from LearningMapService.get_all_region_stats()
        """
        for stats in stats_list:
            region = MapRegion(stats["region"])
            self._region_stats[region] = stats
            
            # Find and update label
            label_id = f"label_{region.value}"
            for item in self.items():
                if item.data(0) == label_id and hasattr(item, 'setHtml'):
                    config = REGION_CONFIG[region]
                    mastered = stats.get("mastered", 0)
                    total = stats.get("total", 0)
                    percent = stats.get("percent_complete", 0)
                    
                    # Determine status color
                    if total == 0:
                        status_color = "rgba(255,255,255,0.3)"
                    elif percent >= 100:
                        status_color = "#ffd93d"  # Gold
                    elif percent > 0:
                        status_color = "#4ecdc4"  # Cyan
                    else:
                        status_color = "rgba(255,255,255,0.7)"
                    
                    item.setHtml(f"""
                        <div style="text-align: center;">
                            <span style="font-size: 32px;">{config['icon']}</span><br/>
                            <span style="font-size: 18px; font-weight: bold; color: white;">
                                {config['name']}
                            </span><br/>
                            <span style="font-size: 12px; color: {status_color};">
                                {mastered}/{total} ✅ ({percent:.0f}%)
                            </span>
                        </div>
                    """)
                    break
    
    def center_of_region(self, region: MapRegion):
        """Get center point of a region."""
        rect = self.get_region_rect(region)
        return rect.center()
    
    # ============ Node Management ============
    
    def load_nodes(self, progress_list, grammar_dict: dict[int, tuple]):
        """Load grammar nodes from progress data.
        
        Args:
            progress_list: List of LearningProgress records
            grammar_dict: Dict of grammar_id -> (title, level) tuples
        """
        # Import here to avoid circular imports
        from frontend.ui.widgets.learning_map.grammar_node import GrammarNode
        from frontend.ui.widgets.learning_map.path_line import PathLine
        
        # Clear existing nodes
        self.clear_nodes()
        
        # Group progress by region for layout
        region_progress: dict[MapRegion, list] = {r: [] for r in MapRegion}
        
        for progress in progress_list:
            grammar_info = grammar_dict.get(progress.grammar_id)
            if grammar_info:
                title, level = grammar_info
                region = get_region_from_level(level)
                region_progress[region].append((progress, title))
        
        # Create nodes for each region
        prev_node = None
        
        for region in MapRegion:
            rect = self._region_bounds[region]
            items = region_progress[region]
            
            # Sort by order_in_region
            items.sort(key=lambda x: x[0].order_in_region)
            
            for i, (progress, title) in enumerate(items):
                # Calculate grid-based position within region for better distribution
                import math
                center_x = rect.center().x()
                center_y = rect.center().y() + 50  # Offset from label
                
                # Improved spiral layout with wider spacing
                angle = i * 0.6 + math.pi / 2  # Wider angle step
                radius = 100 + (i // 6) * 80  # Faster expansion, fewer nodes per ring
                
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle) * 0.7  # Less vertical compression
                
                # Create node
                node = GrammarNode(
                    grammar_id=progress.grammar_id,
                    title=title,
                    status=MapStatus(progress.map_status),
                    is_boss=progress.is_boss_node,
                    progress_percent=(progress.correct_count / max(progress.attempts, 1) * 100)
                                     if progress.attempts > 0 else 0,
                )
                node.setPos(x, y)
                
                # Connect signal
                node.signals.clicked.connect(self._on_node_clicked)
                
                # Add to scene
                self.addItem(node)
                self._nodes[progress.grammar_id] = node
                
                # Create path from previous node
                if prev_node is not None and i > 0:
                    is_unlocked = progress.map_status != MapStatus.LOCKED.value
                    path = PathLine(prev_node.scenePos(), node.scenePos(), is_unlocked)
                    self.addItem(path)
                    self._paths.append(path)
                
                prev_node = node
    
    def clear_nodes(self):
        """Remove all nodes and paths."""
        for node in self._nodes.values():
            self.removeItem(node)
        self._nodes.clear()
        
        for path in self._paths:
            self.removeItem(path)
        self._paths.clear()
    
    def get_node(self, grammar_id: int):
        """Get a node by grammar ID."""
        return self._nodes.get(grammar_id)
    
    def update_node_status(self, grammar_id: int, status: MapStatus, progress: float = None):
        """Update a specific node's visual state."""
        node = self._nodes.get(grammar_id)
        if node:
            node.set_status(status)
            if progress is not None:
                node.set_progress(progress)
    
    def _on_node_clicked(self, grammar_id: int):
        """Handle node click - emit signal."""
        print(f"[MapScene] Node clicked, relaying grammar_id: {grammar_id}")
        self.signals.node_clicked.emit(grammar_id)

