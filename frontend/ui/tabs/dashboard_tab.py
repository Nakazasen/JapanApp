"""Dashboard Tab - Gamification with Contribution Heatmap and Stats Cards.

This tab displays user progress statistics and a GitHub-style contribution graph
to motivate learning through visual feedback and streak tracking.
"""
from datetime import datetime, timedelta
from typing import Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPointF

from frontend.services import get_stats_service
from frontend.utils.async_helpers import run_async
from frontend.ui.widgets.loading_overlay import LoadingOverlayManager, SkeletonManager, SkeletonStatCard
from frontend.ui.mixins.accessibility_mixin import A11yColors, setup_accessible_name
from frontend.ui.styles.theme import ThemeColors


class StatCard(QFrame):
    """A styled card displaying a statistic with icon and value."""
    
    def __init__(self, icon: str, title: str, value: str = "0", color: str = "#3498db", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setup_ui(icon, title, value, color)
        self.apply_shadow()
    
    def setup_ui(self, icon: str, title: str, value: str, color: str):
        """Setup the card UI."""
        self.setFixedSize(210, 130)
        # Use theme colors
        self.setStyleSheet(f"""
            #statCard {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 16px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            #statCard:hover {{
                border: 1px solid {color};
                background-color: {ThemeColors.BG_TERTIARY};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Icon and title row
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 12px;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value with shadow/glow effect
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {color};
            font-size: 36px;
            font-weight: 900;
            font-family: 'Segoe UI', sans-serif;
        """)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    
    def apply_shadow(self):
        """Apply drop shadow effect."""
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)
    
    def set_value(self, value: str):
        """Update the displayed value."""
        self.value_label.setText(value)

    def enterEvent(self, event):
        """Hover enter: Lift up card and increase shadow."""
        # Animate shadow
        self.anim_shadow = QPropertyAnimation(self.shadow, b"offset")
        self.anim_shadow.setDuration(200)
        self.anim_shadow.setStartValue(self.shadow.offset())
        self.anim_shadow.setEndValue(QPointF(0, 8))
        self.anim_shadow.setEasingCurve(QEasingCurve.OutQuad)
        self.anim_shadow.start()
        
        # Animate blur
        self.anim_blur = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim_blur.setDuration(200)
        self.anim_blur.setStartValue(self.shadow.blurRadius())
        self.anim_blur.setEndValue(30)
        self.anim_blur.start()
        
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hover leave: Restore card position and shadow."""
        # Animate shadow back
        self.anim_shadow = QPropertyAnimation(self.shadow, b"offset")
        self.anim_shadow.setDuration(200)
        self.anim_shadow.setStartValue(self.shadow.offset())
        self.anim_shadow.setEndValue(QPointF(0, 4))
        self.anim_shadow.setEasingCurve(QEasingCurve.OutQuad)
        self.anim_shadow.start()
        
        # Animate blur back
        self.anim_blur = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim_blur.setDuration(200)
        self.anim_blur.setStartValue(self.shadow.blurRadius())
        self.anim_blur.setEndValue(20)
        self.anim_blur.start()
        
        super().leaveEvent(event)


class HeatmapCell(QFrame):
    """A single cell in the contribution heatmap."""
    
    # Updated colors to match theme blue/slate vibe
    # Level 0 is BG_SECONDARY (empty) or BG_TERTIARY
    COLORS = {
        0: ThemeColors.BG_TERTIARY,
        1: "#1E3A8A",      # Blue 900
        2: "#1D4ED8",      # Blue 700
        3: "#3B82F6",      # Blue 500
        4: "#60A5FA",      # Blue 400
    }
    
    # Premium Green variant (GitHub style) if needed, but Blue fits better with the theme
    GREEN_COLORS = {
        0: ThemeColors.BG_TERTIARY,
        1: "#064E3B",      # Emerald 900
        2: "#047857",      # Emerald 700
        3: "#10B981",      # Emerald 500
        4: "#34D399",      # Emerald 400
    }
    
    def __init__(self, date: str, count: int, is_today: bool = False, parent=None):
        super().__init__(parent)
        self.date = date
        self.count = count
        self.is_today = is_today
        self.setup_ui()
    
    def setup_ui(self):
        """Setup cell appearance."""
        self.setFixedSize(13, 13)
        
        # Determine color level
        if self.count == 0:
            level = 0
        elif self.count <= 3:
            level = 1
        elif self.count <= 10:
            level = 2
        elif self.count <= 20:
            level = 3
        else:
            level = 4
        
        color = self.COLORS[level]
        
        # Style for today or fallback border for empty cells
        border_style = f"border: 1px solid {ThemeColors.BG_PRIMARY};"
        if self.is_today:
            border_style = f"border: 2px solid {ThemeColors.ACCENT};" # Highlight today
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 2px;
                {border_style}
            }}
            QFrame:hover {{
                border: 1px solid #ffffff;
                background-color: {color};
            }}
        """)
        
        # Format date for tooltip
        try:
            dt = datetime.fromisoformat(self.date)
            formatted_date = f"ngày {dt.day}/{dt.month}/{dt.year}"
        except:
            formatted_date = self.date
        
        # Set tooltip
        self.setToolTip(f"{formatted_date}: {self.count} hoạt động")


class ContributionHeatmap(QWidget):
    """GitHub-style contribution heatmap widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activity_map: Dict[str, int] = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the heatmap UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        
        # Title with Icon
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 5)
        title = QLabel("📊 HOẠT ĐỘNG HỌC TẬP")
        title.setStyleSheet("color: #f0a500; font-size: 13px; font-weight: 900; letter-spacing: 1px;")
        header.addWidget(title)
        header.addStretch()
        main_layout.addLayout(header)
        
        # The heatmap container
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a stretchable container to make sure grid doesn't expand weirdly
        grid_wrapper = QWidget()
        grid_wrapper.setLayout(self.grid_layout)
        main_layout.addWidget(grid_wrapper)
        
        # Legend with labels
        footer = QHBoxLayout()
        footer.setContentsMargins(35, 10, 0, 0) # Align with the start of cells
        
        hint = QLabel("Học ít nhất 1 bài để duy trì chuỗi màu xanh!")
        hint.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        footer.addWidget(hint)
        footer.addStretch()
        
        legend_label = QLabel("Ít")
        legend_label.setStyleSheet("color: #888; font-size: 11px;")
        footer.addWidget(legend_label)
        
        for level in range(5):
            cell = QFrame()
            cell.setFixedSize(11, 11)
            cell.setStyleSheet(f"background-color: {HeatmapCell.GREEN_COLORS[level]}; border-radius: 2px;")
            footer.addWidget(cell)
        
        more_label = QLabel("Nhiều")
        more_label.setStyleSheet("color: #888; font-size: 11px;")
        footer.addWidget(more_label)
        
        main_layout.addLayout(footer)
    
    def update_data(self, activity_map: Dict[str, int]):
        """Update heatmap with new activity data."""
        self.activity_map = activity_map
        self.render_grid()
    
    def render_grid(self):
        """Render the grid with integrated day labels and fixed month logic."""
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Constants
        CELL_COL_START = 1
        MONTH_ROW = 0
        TOTAL_WEEKS = 53
        
        # Add Day Labels (Col 0)
        labels_vi = ["", "T2", "", "T4", "", "T6", "", ""]
        for i, text in enumerate(labels_vi):
            if text:
                lbl = QLabel(text)
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                lbl.setStyleSheet("color: #888; font-size: 9px; font-weight: bold; margin-right: 5px;")
                lbl.setFixedWidth(25)
                # Row i corresponds to the day (starts from 1 for cells)
                self.grid_layout.addWidget(lbl, i, 0)
        
        # Calculate dates
        today = datetime.now().date()
        # Find start date: 52 weeks ago, aligned to the start of the week (Monday)
        # Weekday: Mon=0, ..., Sun=6
        start_date = today - timedelta(days=today.weekday() + 7 * (TOTAL_WEEKS - 1))
        
        # Month labels tracking
        month_vns = ["Th1", "Th2", "Th3", "Th4", "Th5", "Th6", "Th7", "Th8", "Th9", "Th10", "Th11", "Th12"]
        last_month_col = -5 # Ensure first month has space
        
        # 1. Fill Cells and Track Months
        for week in range(TOTAL_WEEKS):
            # Check for month change at the start of each week
            monday_of_week = start_date + timedelta(weeks=week)
            sunday_of_week = monday_of_week + timedelta(days=6)
            
            # If month changes within this week, or if it's the first week
            if monday_of_week.month != (monday_of_week - timedelta(days=7)).month or week == 0:
                # Add month label if there's enough space (at least 2 weeks from last month label)
                if week - last_month_col >= 3:
                     month_label = QLabel(month_vns[monday_of_week.month - 1])
                     month_label.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
                     self.grid_layout.addWidget(month_label, MONTH_ROW, week + CELL_COL_START, 1, 4)
                     last_month_col = week
            
            # Fill the 7 days
            for day_idx in range(7):
                current_date = monday_of_week + timedelta(days=day_idx)
                
                if current_date > today:
                    # Future cell
                    cell = QFrame()
                    cell.setFixedSize(13, 13)
                    cell.setStyleSheet("background-color: #1a1a1a; border-radius: 2px; border: 1px solid #141414;")
                else:
                    date_str = current_date.isoformat()
                    count = self.activity_map.get(date_str, 0)
                    is_today = (current_date == today)
                    cell = HeatmapCell(date_str, count, is_today=is_today)
                
                # Add to grid: row = day_idx + 1 (because row 0 is months), col = week + 1 (because col 0 is days)
                self.grid_layout.addWidget(cell, day_idx + 1, week + CELL_COL_START)


from frontend.core.user_settings import UserSettings

class DashboardTab(QWidget):
    """Dashboard tab with stats cards and contribution heatmap."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats_service = get_stats_service()
        self.settings = UserSettings() # New
        self.loading_manager = LoadingOverlayManager(self)
        self.skeleton_manager = None
        self._is_loading = False
        self.cards = [] # List to track dynamic cards
        self.setup_ui()
        self._setup_accessibility()
        self._setup_skeleton_loading()
        self.load_stats()
    
    def setup_ui(self):
        """Setup the dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Header
        self.header = QLabel("🎯 Dashboard")
        self.header.setStyleSheet("""
            color: #fff;
            font-size: 28px;
            font-weight: bold;
        """)
        main_layout.addWidget(self.header)
        
        subtitle = QLabel("Theo dõi tiến độ học tập và duy trì chuỗi ngày học!")
        subtitle.setStyleSheet(f"color: {A11yColors.TEXT_SECONDARY}; font-size: 14px;")
        main_layout.addWidget(subtitle)
        
        # Today's date label
        days_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        now = datetime.now()
        day_name = days_vi[now.weekday()]
        today_str = f"{day_name}, ngày {now.strftime('%d/%m/%Y')}"
        
        self.today_label = QLabel(f"📅 Hôm nay: {today_str}")
        self.today_label.setStyleSheet("color: #2ecc71; font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.today_label)
        
        # Stats cards row (Container)
        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(16)
        main_layout.addWidget(self.cards_container)
        
        # Heatmap section
        heatmap_frame = QFrame()
        heatmap_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 16px;
                border: 1px solid {ThemeColors.BORDER};
            }}
        """)
        
        heatmap_layout = QVBoxLayout(heatmap_frame)
        heatmap_layout.setContentsMargins(20, 16, 20, 16)
        
        self.heatmap = ContributionHeatmap()
        heatmap_layout.addWidget(self.heatmap)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        heatmap_frame.setGraphicsEffect(shadow)
        
        main_layout.addWidget(heatmap_frame)
        
        # Motivational message
        self.motivation_label = QLabel("")
        self.motivation_label.setStyleSheet("""
            color: #888;
            font-size: 14px;
            font-style: italic;
        """)
        self.motivation_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.motivation_label)
        
        main_layout.addStretch()

    def render_stat_cards(self, stats: dict):
        """Dynamically create cards based on language."""
        # Clear existing
        for card in self.cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.cards = []
        
        lang = self.settings.current_language
        self.header.setText(f"🎯 {'English Workspace' if lang == 'en' else '学習ダッシュボード'}")

        # Helper to add card with accessibility
        def add_card(icon, title, value, color, a11y_title, a11y_desc):
            card = StatCard(icon, title, value, color)
            setup_accessible_name(card, a11y_title, a11y_desc)
            self.cards.append(card)

        # Shared: Streak
        streak = stats.get("current_streak", 0)
        add_card("🔥", "Chuỗi ngày", str(streak), "#ff9500", "Chuỗi ngày học", "Số ngày học liên tục")
        
        if lang == 'en':
            add_card("📚", "Vocab (EN)", str(stats.get("total_vocab", 0)), "#3498db", "Tổng từ vựng", "Tổng số từ vựng Tiếng Anh đã thêm")
            add_card("🏆", "TOEIC Est.", f"{stats.get('toeic_score', 0)}", "#9b59b6", "Điểm TOEIC", "Điểm TOEIC dự kiến")
            add_card("🎯", "Accuracy", f"{stats.get('accuracy', 0)}%", "#27ae60", "Độ chính xác", "Phần trăm trả lời đúng")
        else: # Japanese
            add_card("⛩️", "Kanji", str(stats.get("kanji_count", 0)), "#e74c3c", "Số lượng Kanji", "Số lượng chữ Hán đã học")
            add_card("🎓", "JLPT Level", stats.get("jlpt_level", "N/A"), "#f1c40f", "Cấp độ JLPT", "Cấp độ JLPT dự kiến")
            add_card("📚", "Vocab (JP)", str(stats.get("total_vocab", 0)), "#3498db", "Tổng từ vựng", "Tổng số từ vựng Tiếng Nhật đã thêm")

        # Shared: Due
        add_card("⏰", "Cần ôn", str(stats.get("due_today", 0)), "#e74c3c", "Cần ôn hôm nay", "Số thẻ cần ôn tập hôm nay")

        for card in self.cards:
            self.cards_layout.addWidget(card)
        self.cards_layout.addStretch()

    def load_stats(self):
        """Load dashboard statistics from API."""
        self.loading_manager.show("Đang tải thống kê...")
        lang = self.settings.current_language
        
        async def fetch_stats():
            return self.stats_service.get_dashboard_stats(lang=lang)
        
        def on_stats_loaded(result):
            self.loading_manager.hide()
            if result and result.get("success"):
                self.update_ui(result)
            else:
                print(f"[WARNING DashboardTab] Failed to load stats: {result}")
        
        run_async(fetch_stats, on_stats_loaded)
    
    def update_ui(self, stats: dict):
        """Update UI with loaded statistics."""
        self.render_stat_cards(stats)
            
        # Activity map (Global)
        activity_map = stats.get("activity_map", {})
        self.heatmap.update_data(activity_map)
        
        # Motivational message
        streak = stats.get("current_streak", 0)
        if streak == 0:
            message = "💪 Hãy bắt đầu học ngay hôm nay để tạo chuỗi ngày!"
        elif streak < 7:
            message = f"🔥 Chuỗi {streak} ngày! Hãy giữ vững phong độ!"
        else:
            message = f"🏆 Xuất sắc! Bạn đang duy trì phong độ rất tốt!"
        
        self.motivation_label.setText(message)
    
    def refresh(self):
        """Refresh dashboard data."""
        self.load_stats()
    
    def _setup_accessibility(self):
        """Setup accessibility features for dashboard."""
        # Heatmap accessibility
        
        # Heatmap accessibility
        setup_accessible_name(self.heatmap, "Biểu đồ hoạt động học tập", "Hiển thị hoạt động học tập trong 53 tuần qua")

    def _setup_skeleton_loading(self):
        """Setup skeleton loading indicators for dashboard cards."""
        # Skeleton loading is optional - setup manager if available
        try:
            from frontend.ui.widgets.skeleton_loading_widget import SkeletonLoadingManager
            self.skeleton_manager = SkeletonLoadingManager(self)
        except ImportError:
            self.skeleton_manager = None

