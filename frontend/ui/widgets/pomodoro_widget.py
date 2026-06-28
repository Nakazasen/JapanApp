"""Pomodoro Timer Widget."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QGroupBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, Signal, QSettings
from PySide6.QtGui import QColor, QFont
from frontend.services.pomodoro_service import get_pomodoro_service


class PomodoroWidget(QWidget):
    """Pomodoro timer widget with work and break cycles."""
    
    finished_cycle = Signal(str)  # Emits mode name ('work', 'short_break', 'long_break')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("EnglishApp", "Pomodoro")
        
        # Default durations (seconds)
        self.work_time = self.settings.value("work_duration", 25, type=int) * 60
        self.short_break = self.settings.value("short_break_duration", 5, type=int) * 60
        self.long_break = self.settings.value("long_break_duration", 15, type=int) * 60
        self.cycles_to_long_break = 4
        
        self.remaining_time = self.work_time
        self.is_running = False
        self.current_mode = "work"  # work, short_break, long_break
        self.completed_cycles = 0
        self.pomodoro_service = get_pomodoro_service()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timeout)
        self.timer.setInterval(1000)
        
        self._init_ui()
    
    def _init_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QGroupBox("⏳ Pomodoro")
        self.container.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                background-color: #2d2d2d;
                color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        container_layout = QVBoxLayout(self.container)
        
        # Mode Label
        self.mode_label = QLabel("🔥 SẴN SÀNG HỌC")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 14px;")
        container_layout.addWidget(self.mode_label)
        
        # Timer Label
        self.timer_label = QLabel("25:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #fff; font-family: 'Consolas', monospace;")
        container_layout.addWidget(self.timer_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #404040;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setRange(0, self.work_time)
        self.progress_bar.setValue(self.work_time)
        container_layout.addWidget(self.progress_bar)
        
        # Control Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Bắt đầu")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.start_btn.clicked.connect(self._toggle_timer)
        btn_layout.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.reset_btn.clicked.connect(self._reset_timer)
        btn_layout.addWidget(self.reset_btn)
        
        container_layout.addLayout(btn_layout)
        
        # Cycles Label
        self.cycles_label = QLabel("Chu kỳ: 0/4")
        self.cycles_label.setAlignment(Qt.AlignCenter)
        self.cycles_label.setStyleSheet("color: #888; font-size: 11px;")
        container_layout.addWidget(self.cycles_label)
        
        # New Stats Label
        self.stats_label = QLabel("Hôm nay: 0 🍅 | Tổng: 0 🍅")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #2ecc71; font-size: 11px; font-weight: bold; margin-top: 5px;")
        container_layout.addWidget(self.stats_label)
        
        layout.addWidget(self.container)
        self.setFixedHeight(220)
        self._refresh_stats()
    
    def _toggle_timer(self):
        """Start or pause the timer."""
        if self.is_running:
            self.timer.stop()
            self.start_btn.setText("▶️ Tiếp tục")
            self.is_running = False
        else:
            self.timer.start()
            self.start_btn.setText("⏸️ Tạm dừng")
            self.is_running = True
            
    def _reset_timer(self):
        """Reset the current timer."""
        self.timer.stop()
        self.is_running = False
        self.start_btn.setText("▶️ Bắt đầu")
        
        if self.current_mode == "work":
            self.remaining_time = self.work_time
        elif self.current_mode == "short_break":
            self.remaining_time = self.short_break
        else:
            self.remaining_time = self.long_break
            
        self._update_display()

    def _on_timeout(self):
        """Handle 1s interval."""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self._update_display()
        else:
            # Time up!
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText("▶️ Bắt đầu")
            
            # Switch modes
            self._switch_mode()
            
    def _switch_mode(self):
        """Switch between work and break modes."""
        old_mode = self.current_mode
        
        if self.current_mode == "work":
            self.completed_cycles += 1
            
            # Log to DB
            duration = self.work_time // 60
            self.pomodoro_service.log_session(duration, mode="work")
            self._refresh_stats()
            
            if self.completed_cycles % self.cycles_to_long_break == 0:
                self.current_mode = "long_break"
                self.remaining_time = self.long_break
                self.mode_label.setText("🛋️ NGHỈ DÀI")
                self.mode_label.setStyleSheet("color: #9b59b6; font-weight: bold; font-size: 14px;")
                self.container.setStyleSheet(self.container.styleSheet().replace("#3498db", "#9b59b6"))
            else:
                self.current_mode = "short_break"
                self.remaining_time = self.short_break
                self.mode_label.setText("☕ NGHỈ NGẮN")
                self.mode_label.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 14px;")
                self.container.setStyleSheet(self.container.styleSheet().replace("#3498db", "#e67e22"))
        else:
            # Break finished, back to work
            self.current_mode = "work"
            self.remaining_time = self.work_time
            self.mode_label.setText("🔥 ĐANG HỌC")
            self.mode_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 14px;")
            self.container.setStyleSheet(self.container.styleSheet().replace("#e67e22", "#3498db").replace("#9b59b6", "#3498db"))
            
        self.finished_cycle.emit(old_mode)
        self._update_display()
        
        # Notify user (simple message box or system sound could go here)
        from PySide6.QtWidgets import QMessageBox
        msg = "Đã đến lúc giải lao!" if old_mode == "work" else "Hết giờ nghỉ! Quay lại học thôi."
        # Don't show blocking message box, maybe just update status or beep
        try:
             import winsound
             winsound.Beep(1000, 500)
        except:
             pass

    def _update_display(self):
        """Update timer label and progress bar."""
        mins = self.remaining_time // 60
        secs = self.remaining_time % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
        
        # Progress
        total = self.work_time if self.current_mode == "work" else (self.short_break if self.current_mode == "short_break" else self.long_break)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(self.remaining_time)
        
        # Color based on mode
        color = "#3498db" if self.current_mode == "work" else ("#e67e22" if self.current_mode == "short_break" else "#9b59b6")
        self.progress_bar.setStyleSheet(self.progress_bar.styleSheet().replace("#3498db", color).replace("#e67e22", color).replace("#9b59b6", color))
        
        self.cycles_label.setText(f"Chu kỳ: {self.completed_cycles % 4}/4 (Tổng: {self.completed_cycles})")

    def _refresh_stats(self):
        """Fetch and display total stats from service."""
        stats = self.pomodoro_service.get_stats()
        today = stats.get("today_count", 0)
        total = stats.get("total_count", 0)
        minutes = stats.get("total_minutes", 0)
        self.stats_label.setText(f"Hôm nay: {today} 🍅 | Tổng: {total} 🍅 ({minutes}p)")

    def reload_settings(self):
        """Reload settings from QSettings."""
        self.work_time = self.settings.value("work_duration", 25, type=int) * 60
        self.short_break = self.settings.value("short_break_duration", 5, type=int) * 60
        self.long_break = self.settings.value("long_break_duration", 15, type=int) * 60
        
        if not self.is_running:
            self._reset_timer()
