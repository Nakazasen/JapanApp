"""LearningMapWidget - Main container for the Learning Map.

Contains:
- Region selector toolbar
- MapView (the zoomable/pannable map)
- Progress summary
- Minimap overlay (optional)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QFrame, QToolButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from frontend.models.learning_progress import MapRegion, REGION_CONFIG
from frontend.services.learning_map_service import LearningMapService
from frontend.ui.widgets.learning_map.map_scene import MapScene
from frontend.ui.widgets.learning_map.map_view import MapView


class LearningMapWidget(QWidget):
    """Main container widget for the Learning Map."""
    
    # Signals
    node_selected = Signal(int)  # Emits grammar_id when node clicked
    region_changed = Signal(str)  # Emits region id when switching
    
    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        
        # Current language filter
        self._lang = lang
        
        # Current region
        self._current_region = MapRegion.A1
        
        # Region buttons
        self._region_buttons: dict[MapRegion, QPushButton] = {}
        
        # Service (lazy loaded)
        self._service: LearningMapService | None = None
        
        # Data loaded flag
        self._data_loaded = False
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the widget layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Map container
        map_container = QFrame()
        map_container.setObjectName("MapContainer")
        map_container.setStyleSheet("""
            #MapContainer {
                background-color: #0f0f1a;
                border: none;
            }
        """)
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scene and view
        self._scene = MapScene()
        self._view = MapView()
        self._view.setScene(self._scene)
        
        # Connect signals
        self._view.zoom_changed.connect(self._on_zoom_changed)
        self._view.region_clicked.connect(self._on_region_selected)
        self._scene.signals.node_clicked.connect(self._on_node_clicked)
        
        map_layout.addWidget(self._view)
        layout.addWidget(map_container, 1)  # Stretch factor 1
    
    def _create_toolbar(self) -> QFrame:
        """Create the region selector toolbar."""
        toolbar = QFrame()
        toolbar.setObjectName("MapToolbar")
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("""
            #MapToolbar {
                background-color: #1a1a2e;
                border-bottom: 1px solid #2d2d4a;
            }
            QPushButton {
                background-color: #2d2d4a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3d3d5a;
            }
            QPushButton:checked {
                background-color: #4ecdc4;
                color: #0f0f1a;
                font-weight: bold;
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("🗺️ Bản đồ Chinh phục")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Region buttons
        for region in MapRegion:
            config = REGION_CONFIG[region]
            btn = QPushButton(f"{config['icon']} {region.name}")
            btn.setCheckable(True)
            btn.setProperty("region", region.value)
            btn.clicked.connect(lambda checked, r=region: self._navigate_to_region(r))
            
            self._region_buttons[region] = btn
            layout.addWidget(btn)
        
        # Set default region selected
        self._region_buttons[MapRegion.A1].setChecked(True)
        
        layout.addStretch()
        
        # Zoom controls
        zoom_label = QLabel("🔍")
        layout.addWidget(zoom_label)
        
        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(50, 200)  # 50% - 200%
        self._zoom_slider.setValue(100)
        self._zoom_slider.setFixedWidth(100)
        self._zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #3d3d5a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -6px 0;
                background: #4ecdc4;
                border-radius: 8px;
            }
        """)
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        layout.addWidget(self._zoom_slider)
        
        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(45)
        layout.addWidget(self._zoom_label)
        
        # Progress summary
        layout.addSpacing(15)
        self._progress_label = QLabel("📈 0/0")
        self._progress_label.setToolTip("Tiến độ tổng thể")
        layout.addWidget(self._progress_label)
        
        return toolbar
    
    # ============ Region Navigation ============
    
    def _navigate_to_region(self, region: MapRegion):
        """Navigate the view to a specific region."""
        # Update button states
        for r, btn in self._region_buttons.items():
            btn.setChecked(r == region)
        
        self._current_region = region
        
        # Get region rectangle and center on it
        rect = self._scene.get_region_rect(region)
        if rect.isValid():
            self._view.fit_to_region(rect)
        
        self.region_changed.emit(region.value)
    
    def _on_region_selected(self, region_id: str):
        """Handle region selection from double-click or keyboard."""
        try:
            region = MapRegion(region_id)
            self._navigate_to_region(region)
        except ValueError:
            pass
    
    # ============ Zoom ============
    
    def _on_zoom_changed(self, level: float):
        """Handle zoom level changes from the view."""
        percent = int(level * 100)
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(percent)
        self._zoom_slider.blockSignals(False)
        self._zoom_label.setText(f"{percent}%")
    
    def _on_zoom_slider_changed(self, value: int):
        """Handle zoom slider changes."""
        self._view.zoom_to(value / 100.0, animated=False)
    
    # ============ Data Loading ============
    
    def _get_service(self) -> LearningMapService:
        """Get or create the service."""
        if self._service is None:
            self._service = LearningMapService()
        return self._service
    
    def _load_data(self):
        """Load progress data and update display."""
        service = self._get_service()
        
        # Ensure progress records exist
        service.ensure_progress_exists()
        
        # Get region stats
        stats = service.get_all_region_stats()
        self._scene.update_region_stats(stats)
        
        # Load grammar nodes
        self._load_grammar_nodes(service)
        
        # Update overall progress label
        overall = service.get_overall_stats()
        mastered = overall.get("mastered", 0)
        total = overall.get("total", 0)
        percent = overall.get("percent_complete", 0)
        self._progress_label.setText(f"📈 {mastered}/{total} ({percent:.0f}%)")
        
        # Navigate to first region
        self._navigate_to_region(MapRegion.A1)
    
    def _load_grammar_nodes(self, service: LearningMapService):
        """Load grammar nodes from database, filtered by language."""
        from sqlmodel import select
        from frontend.models.grammar import GrammarTopic
        from frontend.core.database import engine
        from sqlmodel import Session
        
        # Get all progress records
        progress_list = service.get_all_progress()
        
        # Get grammar titles and levels - FILTERED BY LANGUAGE
        with Session(engine) as session:
            stmt = select(GrammarTopic).where(GrammarTopic.lang == self._lang)
            grammar_items = session.exec(stmt).all()
            grammar_dict = {
                g.id: (g.title or g.pattern, g.level)
                for g in grammar_items
            }
        
        # Filter progress to only include items in grammar_dict
        filtered_progress = [p for p in progress_list if p.grammar_id in grammar_dict]
        
        # Load nodes into scene
        self._scene.load_nodes(filtered_progress, grammar_dict)
    
    def _on_node_clicked(self, grammar_id: int):
        """Handle grammar node click."""
        self.node_selected.emit(grammar_id)
    
    def refresh_data(self):
        """Refresh progress data (call after studying)."""
        self._load_data()
    
    def set_language(self, lang: str):
        """Update the language filter and reload data."""
        if lang != self._lang:
            self._lang = lang
            self._data_loaded = False
            if self.isVisible():
                self._load_data()
    
    def showEvent(self, event):
        """Load data when widget becomes visible (lazy loading)."""
        if not self._data_loaded:
            self._data_loaded = True
            QTimer.singleShot(50, self._load_data)
        super().showEvent(event)
    
    # ============ Cleanup ============
    
    def closeEvent(self, event):
        """Clean up resources."""
        if self._service:
            self._service.close()
        super().closeEvent(event)
