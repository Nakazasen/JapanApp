"""TOEIC Dashboard Tab.

Visualizes progress, estimated scores, and part-wise performance.
"""
from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QProgressBar, QGridLayout, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.ui.styles.theme import ThemeColors
from frontend.utils.async_helpers import run_async
from frontend.ui.widgets.radar_chart import RadarChart


class StatCard(QFrame):
    """Card widget for displaying a single statistic."""
    
    def __init__(self, title: str, value: str, subtext: str = "", color: str = ThemeColors.PRIMARY, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                padding: 16px;
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 13px; font-weight: bold;")
        layout.addWidget(title_lbl)
        
        # Value
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_lbl)
        
        # Subtext
        if subtext:
            self.sub_lbl = QLabel(subtext)
            self.sub_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
            layout.addWidget(self.sub_lbl)
            
    def update_value(self, value: str, subtext: str = ""):
        self.value_lbl.setText(value)
        if hasattr(self, 'sub_lbl') and subtext:
             self.sub_lbl.setText(subtext)


class PartProgressBar(QWidget):
    """Progress bar for a specific TOEIC Part."""
    
    def __init__(self, part_num: int, name: str, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(4)
        
        # Header
        header = QHBoxLayout()
        name_lbl = QLabel(f"Part {part_num}: {name}")
        name_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; font-weight: bold;")
        header.addWidget(name_lbl)
        
        self.stats_lbl = QLabel("0/0 (0%)")
        self.stats_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 12px;")
        header.addWidget(self.stats_lbl, alignment=Qt.AlignRight)
        layout.addLayout(header)
        
        # Bar
        self.bar = QProgressBar()
        self.bar.setFixedHeight(10)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.ACCENT};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.bar)
        
    def update_progress(self, correct: int, total: int):
        if total > 0:
            percent = int((correct / total) * 100)
            self.bar.setValue(percent)
            self.stats_lbl.setText(f"{correct}/{total} ({percent}%)")
            
            # Color code
            if percent >= 80:
                color = ThemeColors.SUCCESS
            elif percent >= 50:
                color = ThemeColors.WARNING
            else:
                color = ThemeColors.DANGER
                
            self.bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {ThemeColors.BG_TERTIARY};
                    border-radius: 5px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 5px;
                }}
            """)
        else:
            self.bar.setValue(0)
            self.stats_lbl.setText("0/0 (0%)")


class ToeicDashboardTab(QWidget):
    """Dashboard tab for TOEIC module."""
    
    def __init__(self):
        super().__init__()
        self.service = get_toeic_listening_service()
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_lbl = QLabel("📊 My TOEIC Progress")
        header_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        main_layout.addWidget(header_lbl)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(24)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # 1. Summary Cards
        self._create_summary_cards()
        
        # 2. Charts & Insights (New Layout: Left=Radar, Right=AI)
        self._create_charts_section()

        # 3. Part Breakdown
        self._create_breakdown_section()
        
        # Refresh button (Temporary, ideally auto-refresh)
        refresh_btn = QLabel("Refreshes automatically")
        refresh_btn.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
        main_layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

    def _create_charts_section(self):
        """Create section with Radar Chart and AI Insights."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Left: Radar Chart
        chart_frame = QFrame()
        chart_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 12px; padding: 10px;")
        cf_layout = QVBoxLayout(chart_frame)
        
        cf_layout.addWidget(QLabel("🎯 Skill Radar"))
        
        self.radar_chart = RadarChart(["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6", "Part 7"], 
                                      [0, 0, 0, 0, 0, 0, 0])
        cf_layout.addWidget(self.radar_chart)
        
        layout.addWidget(chart_frame, stretch=1)
        
        # Right: AI Insights
        self._create_ai_insights_panel(layout)
        
        self.content_layout.addWidget(container)

    def _create_ai_insights_panel(self, parent_layout):
        """Create AI Coach insight card (Refactored to be part of Charts section)."""
        self.ai_card = QFrame()
        self.ai_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                padding: 20px;
                border-left: 4px solid #9b59b6; /* Purple for AI */
            }}
        """)
        ai_layout = QVBoxLayout(self.ai_card)
        ai_layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        header_lbl = QLabel("🤖 AI Performance Coach")
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        header_layout.addWidget(header_lbl)
        
        header_layout.addStretch()
        
        from PySide6.QtWidgets import QPushButton
        self.refresh_ai_btn = QPushButton("✨ Generate Advice")
        self.refresh_ai_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_ai_btn.clicked.connect(self._fetch_ai_advice)
        self.refresh_ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #9b59b6;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #8e44ad; }}
        """)
        header_layout.addWidget(self.refresh_ai_btn)
        
        ai_layout.addLayout(header_layout)
        
        # Content
        self.ai_content = QLabel("Click 'Generate Advice' to get personalized learning strategies based on your weak points.")
        self.ai_content.setWordWrap(True)
        self.ai_content.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 14px; line-height: 1.5;")
        self.ai_content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        ai_layout.addWidget(self.ai_content, stretch=1)
        
        parent_layout.addWidget(self.ai_card, stretch=1)
    
    # Old _create_ai_insights removed/replaced by above logic
    # Keeping helper methods


    def _fetch_ai_advice(self):
        """Fetch advice from Gemini."""
        self.refresh_ai_btn.setEnabled(False)
        self.refresh_ai_btn.setText("Thinking...")
        self.ai_content.setText("Analyzing your statistics... (this may take a few seconds)")
        
        run_async(self.service.generate_ai_advice, self._update_ai_advice)
        
    def _update_ai_advice(self, advice: str):
        self.refresh_ai_btn.setEnabled(True)
        self.refresh_ai_btn.setText("✨ Generate Advice")
        if advice:
            # Simple markdown formatting for bold
            formatted = advice.replace("**", "") # Strip markdown bold for plain label, or use rich text
            self.ai_content.setText(formatted) 
            # Or better, if simple markdown is clean enough
            self.ai_content.setText(advice)
            self.ai_content.setTextFormat(Qt.MarkdownText)
        else:
            self.ai_content.setText("Could not generate advice at this time.")

    def _create_summary_cards(self):
        """Create top-level summary cards."""
        card_layout = QHBoxLayout()
        card_layout.setSpacing(16)
        
        self.score_card = StatCard("ESTIMATED SCORE", "5", "Listening: 5 | Reading: 5", ThemeColors.PRIMARY)
        self.accuracy_card = StatCard("OVERALL ACCURACY", "0%", "0/0 Correct", ThemeColors.INFO)
        self.questions_card = StatCard("QUESTIONS COMPLETED", "0", "Total Answered", ThemeColors.SUCCESS)
        
        card_layout.addWidget(self.score_card)
        card_layout.addWidget(self.accuracy_card)
        card_layout.addWidget(self.questions_card)
        
        self.content_layout.addLayout(card_layout)
        
    def _create_breakdown_section(self):
        """Create breakdown charts."""
        grid = QGridLayout()
        grid.setSpacing(24)
        
        # Listening Column
        listening_frame = QFrame()
        listening_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 12px; padding: 16px;")
        l_layout = QVBoxLayout(listening_frame)
        
        l_header = QLabel("🎧 Listening Skills")
        l_header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY}; margin-bottom: 10px;")
        l_layout.addWidget(l_header)
        
        self.part_bars = {}
        
        part_names = {
            1: "Photographs",
            2: "Question-Response",
            3: "Conversations",
            4: "Talks",
            5: "Incomplete Sentences",
            6: "Text Completion",
            7: "Reading Comprehension"
        }
        
        for i in range(1, 5):
            bar = PartProgressBar(i, part_names[i])
            l_layout.addWidget(bar)
            self.part_bars[i] = bar
            
        l_layout.addStretch()
        grid.addWidget(listening_frame, 0, 0)
        
        # Reading Column
        reading_frame = QFrame()
        reading_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 12px; padding: 16px;")
        r_layout = QVBoxLayout(reading_frame)
        
        r_header = QLabel("📖 Reading Skills")
        r_header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY}; margin-bottom: 10px;")
        r_layout.addWidget(r_header)
        
        for i in range(5, 8):
            bar = PartProgressBar(i, part_names[i])
            r_layout.addWidget(bar)
            self.part_bars[i] = bar
            
        r_layout.addStretch()
        grid.addWidget(reading_frame, 0, 1)
        
        self.content_layout.addLayout(grid)

    def refresh(self):
        """Refresh stats from service."""
        stats = self.service.get_dashboard_stats()
        if not stats:
            return
            
        # Update Cards
        total_score = stats.get("total_score", 10)
        l_score = stats.get("listening_score", 5)
        r_score = stats.get("reading_score", 5)
        self.score_card.update_value(f"{total_score}", f"Listening: {l_score} | Reading: {r_score}")
        
        accuracy = stats.get("accuracy", 0)
        total_correct = stats.get("total_correct", 0)
        total_answered = stats.get("total_answered", 0)
        self.accuracy_card.update_value(f"{accuracy}%", f"{total_correct}/{total_answered} Correct")
        
        self.questions_card.update_value(f"{total_answered}", "Total Questions")
        
        # Update Bars & Radar
        part_stats = stats.get("part_stats", {})
        radar_values = []
        for i in range(1, 8):
            # Bar update
            if i in self.part_bars:
                p_stat = part_stats.get(i, {"correct": 0, "total": 0})
                self.part_bars[i].update_progress(p_stat["correct"], p_stat["total"])
            
            # Radar update
            p_stat = part_stats.get(i, {"correct": 0, "total": 0})
            acc = 0
            if p_stat["total"] > 0:
                acc = (p_stat["correct"] / p_stat["total"]) * 100
            radar_values.append(acc)
            
        # Update Radar
        if hasattr(self, 'radar_chart'):
            self.radar_chart.set_data(
                ["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6", "Part 7"], 
                radar_values
            )

    def showEvent(self, event):
        """Refresh when tab is shown."""
        self.refresh()
        super().showEvent(event)
