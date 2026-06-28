from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QStatusBar, QMessageBox, QDockWidget, QMenu,
    QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication # For theme application

from frontend.ui.widgets.sidebar import SidebarWidget
from frontend.ui.styles.style_manager import StyleManager

from frontend.ui.tabs.vocab_tab import VocabTab
from frontend.ui.tabs.writing_tab import WritingTab
from frontend.ui.tabs.speaking_tab import SpeakingTab
from frontend.ui.tabs.youtube_tab import YouTubeTab
from frontend.ui.tabs.news_tab import NewsTab
from frontend.ui.tabs.reading_tab import ReadingTab
from frontend.ui.tabs.grammar_tab import GrammarTab
from frontend.ui.tabs.kanji_tab import KanjiTab
from frontend.ui.tabs.exam_tab import ExamTab
from frontend.ui.tabs.reading_practice_tab import ReadingPracticeTab
from frontend.ui.tabs.listening_practice_tab import ListeningPracticeTab
from frontend.ui.tabs.toeic_listening_tab import ToeicListeningTab
from frontend.ui.tabs.toeic_reading_tab import ToeicReadingTab
from frontend.ui.tabs.toeic_exam_tab import ToeicExamTab
from frontend.ui.tabs.content_generator_tab import ContentGeneratorTab  # NEW # NEW
from frontend.ui.tabs.toeic_dashboard_tab import ToeicDashboardTab # NEW
from frontend.ui.tabs.settings_tab import SettingsTab
from frontend.ui.widgets.pomodoro_widget import PomodoroWidget
from frontend.ui.tabs.dashboard_tab import DashboardTab
from frontend.ui.tabs.introduction_tab import IntroductionTab
from frontend.ui.widgets.ai_chat_widget import AIChatWidget
from frontend.ui.widgets.toast_widget import get_toast_manager, ToastType
from frontend.ui.mixins.accessibility_mixin import enhance_widget_accessibility, A11yColors


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ứng dụng học Tiếng Anh & Tiếng Nhật - Enterprise Edition")
        self.setMinimumSize(1280, 800)
        
        # Apply Theme
        StyleManager.apply_theme(QApplication.instance())
        
        # Create central widget with Horizontal Layout (Sidebar + Stacked)
        central_widget = QWidget()
        central_widget.setObjectName("content_widget")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Create Sidebar
        self.sidebar = SidebarWidget()
        main_layout.addWidget(self.sidebar)
        
        # 2. Create Stacked Widget (Content Area)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create tabs/pages
        self.dashboard_tab = DashboardTab()
        self.introduction_tab = IntroductionTab()
        self.vocab_tab = VocabTab()
        self.grammar_tab = GrammarTab()
        self.kanji_tab = KanjiTab()
        self.reading_practice_tab = ReadingPracticeTab()
        self.listening_practice_tab = ListeningPracticeTab()
        self.writing_tab = WritingTab()
        self.speaking_tab = SpeakingTab()
        self.exam_tab = ExamTab()
        self.toeic_dashboard_tab = ToeicDashboardTab() # NEW: TOEIC Dashboard
        self.toeic_listening_tab = ToeicListeningTab()  # NEW: TOEIC Listening
        self.toeic_reading_tab = ToeicReadingTab()      # NEW: TOEIC Reading
        self.toeic_exam_tab = ToeicExamTab()            # NEW: TOEIC Exam
        self.content_gen_tab = ContentGeneratorTab()  # NEW
        self.youtube_tab = YouTubeTab()
        self.news_tab = NewsTab()
        self.reading_tab = ReadingTab()
        self.settings_tab = SettingsTab()
        
        # Add pages to Stacked Widget in EXACT order of Sidebar items
        # 0: Dashboard
        self.stacked_widget.addWidget(self.dashboard_tab)
        # 1: Introduction
        self.stacked_widget.addWidget(self.introduction_tab)
        # 2: Vocab
        self.stacked_widget.addWidget(self.vocab_tab)
        # 3: Grammar
        self.stacked_widget.addWidget(self.grammar_tab)
        # 4: Kanji
        self.stacked_widget.addWidget(self.kanji_tab)
        # 5: Reading Practice
        self.stacked_widget.addWidget(self.reading_practice_tab)
        # 6: Listening Practice
        self.stacked_widget.addWidget(self.listening_practice_tab)
        # 7: Writing
        self.stacked_widget.addWidget(self.writing_tab)
        # 8: Speaking
        self.stacked_widget.addWidget(self.speaking_tab)
        # 9: Exam
        self.stacked_widget.addWidget(self.exam_tab)
        # 10: TOEIC Dashboard
        self.stacked_widget.addWidget(self.toeic_dashboard_tab)
        # 11: TOEIC Listening
        self.stacked_widget.addWidget(self.toeic_listening_tab)
        # 12: TOEIC Reading
        self.stacked_widget.addWidget(self.toeic_reading_tab)
        # 13: TOEIC Exam
        self.stacked_widget.addWidget(self.toeic_exam_tab)
        self.stacked_widget.addWidget(self.content_gen_tab)  # NEW index 5 (0:home, 1:dash, 2:list, 3:read, 4:exam, 5:gen)
        # 14: YouTube
        self.stacked_widget.addWidget(self.youtube_tab)
        # 12: News
        self.stacked_widget.addWidget(self.news_tab)
        # 13: Reading Books
        self.stacked_widget.addWidget(self.reading_tab)
        # 14: Settings
        self.stacked_widget.addWidget(self.settings_tab)
        
        # Connect Sidebar to Stacked Widget
        # Connect Sidebar to Stacked Widget
        self.sidebar.page_changed.connect(self._on_sidebar_page_changed)
        
        # Connect tab change to refresh dashboard logic
        self.stacked_widget.currentChanged.connect(self._on_tab_changed)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sẵn sàng")
        
        # Create AI Assistant Side Panel
        self._create_ai_assistant_dock()
        self._create_pomodoro_dock()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Initialize Toast Manager for global notifications
        self.toast_manager = get_toast_manager()
        
        # Apply accessibility enhancements
        self._setup_accessibility()
    
    def _create_pomodoro_dock(self):
        """Create Pomodoro timer dock."""
        self.pomodoro_dock = QDockWidget("🍅 Pomodoro Timer", self)
        self.pomodoro_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.pomodoro_widget = PomodoroWidget()
        self.pomodoro_dock.setWidget(self.pomodoro_widget)
        
        # Add to the right area initially, but stacked or below AI assistant
        self.addDockWidget(Qt.RightDockWidgetArea, self.pomodoro_dock)
        
    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Tệp")
        exit_action = file_menu.addAction("Thoát")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("Chỉnh sửa")
        
        # Refresh action
        refresh_action = edit_menu.addAction("🔄 Làm mới Dashboard")
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_dashboard)
        
        edit_menu.addSeparator()
        
        # Settings action
        settings_action = edit_menu.addAction("⚙️ Cài đặt")
        settings_action.triggered.connect(self._open_settings)
        
        # View menu (new!)
        view_menu = menubar.addMenu("Xem")
        
        # Tab navigation
        # Tab navigation
        dashboard_action = view_menu.addAction("🎯 Dashboard")
        dashboard_action.setShortcut("Ctrl+1")
        dashboard_action.triggered.connect(lambda: self.sidebar.set_current_index(0))
        
        vocab_action = view_menu.addAction("📚 Từ vựng")
        vocab_action.setShortcut("Ctrl+2")
        vocab_action.triggered.connect(lambda: self.sidebar.set_current_index(2))
        
        reading_action = view_menu.addAction("📖 Đọc sách")
        reading_action.setShortcut("Ctrl+6")
        reading_action.triggered.connect(lambda: self.sidebar.set_current_index(17))
        
        view_menu.addSeparator()
        
        # AI Assistant Toggle
        self.ai_action = view_menu.addAction("🤖 Trợ lý AI")
        self.ai_action.setCheckable(True)
        self.ai_action.setChecked(True)
        self.ai_action.setShortcut("Ctrl+I")
        self.ai_action.triggered.connect(self._toggle_ai_assistant)
        
        # Pomodoro Toggle
        self.pomo_action = view_menu.addAction("🍅 Pomodoro Timer")
        self.pomo_action.setCheckable(True)
        self.pomo_action.setChecked(True)
        self.pomo_action.setShortcut("Ctrl+M")
        self.pomo_action.triggered.connect(lambda: self.pomodoro_dock.setVisible(not self.pomodoro_dock.isVisible()))
        
        # Help menu
        help_menu = menubar.addMenu("Trợ giúp")
        
        shortcuts_action = help_menu.addAction("⌨️ Phím tắt")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        
        help_menu.addSeparator()
        
        about_action = help_menu.addAction("Giới thiệu")
        about_action.triggered.connect(self._show_about)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Giới thiệu",
            "Ứng dụng học Tiếng Anh & Tiếng Nhật\n\n"
            "Version 1.0.0\n\n"
            "Desktop app với AI hỗ trợ học ngôn ngữ"
        )
    
    def _open_settings(self):
        """Open settings tab."""
        # Find settings tab index
        self.sidebar.set_current_index(18) # Fallback if using old index, but better to use target system
    
    def _on_sidebar_page_changed(self, target):
        """Handle page change from sidebar."""
        if isinstance(target, int):
            self.stacked_widget.setCurrentIndex(target)
        elif isinstance(target, str):
            if target == "settings":
                self.stacked_widget.setCurrentWidget(self.settings_tab)
            # Add other string targets here if needed
        
        # Refresh logic
        current_index = self.stacked_widget.currentIndex()
        self._on_tab_changed(current_index)

    def _refresh_dashboard(self):
        """Refresh dashboard data."""
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
            self.update_status("Đã làm mới dữ liệu")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
⌨️ PHÍM TẮT

📌 ĐIỀU HƯỚNG:
  • Ctrl+1: Dashboard
  • Ctrl+2: Từ vựng  
  • Ctrl+6: Đọc/Nghe sách
  • F5: Làm mới Dashboard

📌 HỌC TẬP (Study Session):
  • Space/Enter: Lật thẻ
  • 1: Đánh giá "Lại"
  • 2: Đánh giá "Khó"
  • 3: Đánh giá "Tốt"
  • 4: Đánh giá "Dễ"
  • S: Bỏ qua thẻ
  • Esc: Đóng

📌 CHUNG:
  • Ctrl+Q: Thoát ứng dụng
"""
        QMessageBox.information(self, "Phím tắt", shortcuts_text)
    
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_bar.showMessage(message, 3000)  # Show for 3 seconds
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - refresh dashboard when switching to it."""
        if index == 0 and hasattr(self, 'dashboard_tab'):
            self.dashboard_tab.refresh()

    def _create_ai_assistant_dock(self):
        """Create and dock the AI Assistant widget."""
        self.ai_dock = QDockWidget("Trợ lý AI", self)
        self.ai_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self.ai_assistant = AIChatWidget(self)
        self.ai_dock.setWidget(self.ai_assistant)
        
        # Connect signals
        self.ai_assistant.request_settings.connect(self._open_settings)
        self.ai_assistant.request_context.connect(self._provide_ai_context)
        
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_dock)
        
    def _toggle_ai_assistant(self, checked: bool):
        """Toggle AI Assistant visibility."""
        if hasattr(self, 'ai_dock'):
            self.ai_dock.setVisible(checked)
            self.update_status(f"{'Hiện' if checked else 'Ẩn'} trợ lý AI")

    def _provide_ai_context(self):
        """Gather context from current tab and provide to AI Assistant."""
        current_tab = self.stacked_widget.currentWidget()
        context = ""
        
        if hasattr(current_tab, "get_current_word_context"):
            context = current_tab.get_current_word_context()
            
        if context:
            self.ai_assistant.current_context = context
            self.update_status("Đã nạp ngữ cảnh từ vựng cho AI")
    
    def _setup_accessibility(self):
        """Setup accessibility features for the main window."""
        # Set accessible name for main window
        self.setAccessibleName("Ứng dụng học Tiếng Anh và Tiếng Nhật")
        
        # Set accessible names for tab widget
        self.sidebar.setAccessibleName("Thanh điều hướng bên trái")
        
        # Apply focus indicators to tab bar
        # tab_bar = self.tab_widget.tabBar()
        # tab_bar.setAccessibleName("Thanh tab điều hướng")
        
        # Apply accessibility enhancements to docks
        if hasattr(self, 'ai_dock'):
            self.ai_dock.setAccessibleName("Panel trợ lý AI")
        if hasattr(self, 'pomodoro_dock'):
            self.pomodoro_dock.setAccessibleName("Panel Pomodoro Timer")
    
    def show_toast(self, message: str, toast_type: str = "info"):
        """Show a toast notification.
        
        Args:
            message: Message to display
            toast_type: One of 'success', 'error', 'warning', 'info'
        """
        type_map = {
            "success": ToastType.SUCCESS,
            "error": ToastType.ERROR,
            "warning": ToastType.WARNING,
            "info": ToastType.INFO
        }
        t_type = type_map.get(toast_type, ToastType.INFO)
        self.toast_manager.show_toast(message, t_type)
    
    def show_success(self, message: str):
        """Show success toast."""
        self.toast_manager.show_success(message)
        
    def show_error(self, message: str):
        """Show error toast."""
        self.toast_manager.show_error(message)

