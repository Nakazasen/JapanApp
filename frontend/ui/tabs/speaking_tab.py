"""Speaking Tab with Shadowing Library and Pronunciation Test.

Combines both shadowing practice (AI-generated scripts + TTS playback)
and pronunciation testing (recording + AI scoring) in a unified interface.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QFrame, QScrollArea, QStackedWidget, QListWidget,
    QListWidgetItem, QSlider, QMessageBox, QTabWidget, QTextEdit, QTextBrowser
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from typing import Optional, Dict, Any, List
import os
import tempfile
import threading
import base64
import wave
import time

from frontend.core.shadowing_manager import get_shadowing_manager, ShadowingManager
from frontend.services.shadowing_service import get_shadowing_service
from frontend.services.speaking_service import get_speaking_service
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin
from frontend.utils.async_helpers import run_async
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning

# Audio recording libraries
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    try:
        import sounddevice as sd
        import numpy as np
        HAS_SOUNDDEVICE = True
    except ImportError:
        HAS_SOUNDDEVICE = False


class GenerateScriptWorker(QThread):
    """Worker thread for generating shadowing scripts."""
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, topic: str, level: str, num_sentences: int = 5):
        super().__init__()
        self.topic = topic
        self.level = level
        self.num_sentences = num_sentences
    
    def run(self):
        try:
            service = get_shadowing_service()
            result = service.generate_full_lesson(
                self.topic, self.level, self.num_sentences
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SpeakingTab(QWidget):
    """Speaking Tab with Shadowing Library and Pronunciation Test sub-tabs."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the main UI with QTabWidget for sub-tabs."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self._apply_styles()
        self.setObjectName("SpeakingTab")
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tab widget for sub-modes
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #0f0f1b; }
            QTabBar::tab {
                background: #1a1a2e; color: #9ca3af;
                padding: 12px 24px; margin-right: 2px;
                border-top-left-radius: 8px; border-top-right-radius: 8px;
            }
            QTabBar::tab:selected { background: #2563eb; color: white; }
            QTabBar::tab:hover:!selected { background: #374151; }
        """)
        
        # Tab 1: Shadowing Library
        self.shadowing_widget = ShadowingLibraryWidget()
        self.mode_tabs.addTab(self.shadowing_widget, "📚 Shadowing Library")
        
        # Tab 2: Pronunciation Test
        self.pronunciation_widget = PronunciationTestWidget()
        self.mode_tabs.addTab(self.pronunciation_widget, "🎤 Pronunciation Test")
        
        main_layout.addWidget(self.mode_tabs, 1)
    
    def _apply_styles(self):
        """Apply global styles."""
        self.setStyleSheet("""
            QWidget#SpeakingTab { background-color: #0f0f1b; }
            QFrame#Header { background-color: #1a1a2e; border-bottom: 1px solid #2e2e42; }
            QLabel { color: #e0e0e0; }
            QLabel#Title { font-size: 22px; font-weight: 800; color: #f0a500; }
        """)
    
    def _create_header(self) -> QFrame:
        """Create header bar."""
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("🎤 SMART SPEECH LAB")
        title.setObjectName("Title")
        layout.addWidget(title)
        layout.addStretch()
        
        return header


class ShadowingLibraryWidget(QWidget, TextContextMenuMixin):
    """Widget for Shadowing Library functionality."""
    
    VIEW_LIBRARY = 0
    VIEW_PLAYER = 1
    
    def __init__(self):
        super().__init__()
        self.manager: ShadowingManager = get_shadowing_manager()
        self.current_lesson: Optional[Dict[str, Any]] = None
        self.current_audio_path: Optional[str] = None
        self.is_new_lesson: bool = False
        self.generate_worker: Optional[GenerateScriptWorker] = None
        
        # QMediaPlayer setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        
        # Connect mixin player to this player for shared TTS
        self._mixin_media_player = self.player
        self._mixin_audio_output = self.audio_output
        
        self._init_ui()
        self._load_library()
    
    def _init_ui(self):
        """Initialize the shadowing UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self._apply_styles()
        
        # Stacked widget for views
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        self.stack.addWidget(self._create_library_view())
        self.stack.addWidget(self._create_player_view())
        self.stack.setCurrentIndex(self.VIEW_LIBRARY)
    
    def _apply_styles(self):
        """Apply widget styles."""
        self.setStyleSheet("""
            QPushButton#ActionBtn {
                background-color: #10b981; color: white;
                border: none; border-radius: 8px;
                padding: 12px 24px; font-weight: bold; font-size: 14px;
            }
            QPushButton#ActionBtn:hover { background-color: #059669; }
            QPushButton#ActionBtn:disabled { background-color: #374151; color: #6b7280; }
            
            QPushButton#SecondaryBtn {
                background-color: #374151; color: #d1d5db;
                border: 1px solid #4b5563; border-radius: 6px;
                padding: 10px 20px; font-weight: 500;
            }
            QPushButton#SecondaryBtn:hover { background-color: #4b5563; }
            
            QPushButton#DeleteBtn {
                background-color: transparent; color: #ef4444;
                border: none; padding: 4px; font-size: 16px;
            }
            QPushButton#DeleteBtn:hover { color: #f87171; }
            
            QListWidget { 
                background-color: #16213e; border: none; 
                border-radius: 10px; padding: 8px;
            }
            QListWidget::item { 
                background-color: #1e293b; border-radius: 8px; 
                margin: 4px; padding: 12px;
            }
            QListWidget::item:selected { background-color: #2563eb; }
            QListWidget::item:hover { background-color: #334155; }
            
            QLineEdit, QComboBox {
                background-color: #1e293b; color: white;
                border: 1px solid #374151; border-radius: 6px;
                padding: 10px 14px; font-size: 14px;
            }
            
            QFrame#ScriptCard {
                background-color: #1e293b; border-radius: 12px;
                border: 1px solid #374151; padding: 16px;
            }
            
            QSlider::groove:horizontal {
                height: 6px; background: #374151; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6; width: 16px; height: 16px;
                border-radius: 8px; margin: -5px 0;
            }
            QSlider::sub-page:horizontal { background: #3b82f6; border-radius: 3px; }
        """)
    
    def _create_library_view(self) -> QWidget:
        """Create library list view."""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(16)
        
        # Top bar
        top_bar = QHBoxLayout()
        lib_title = QLabel("📚 Thư viện Shadowing của bạn")
        lib_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        top_bar.addWidget(lib_title)
        top_bar.addStretch()
        
        self.btn_new = QPushButton("➕ Bài tập mới")
        self.btn_new.setObjectName("ActionBtn")
        self.btn_new.clicked.connect(self._on_new_practice)
        top_bar.addWidget(self.btn_new)
        layout.addLayout(top_bar)
        
        # Lessons list
        self.lessons_list = QListWidget()
        self.lessons_list.itemClicked.connect(self._on_lesson_clicked)
        layout.addWidget(self.lessons_list, 1)
        
        # Empty state
        self.empty_label = QLabel("Chưa có bài tập nào.\nBấm '➕ Bài tập mới' để bắt đầu!")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #6b7280; font-size: 16px;")
        layout.addWidget(self.empty_label)
        
        return view
    
    def _create_player_view(self) -> QWidget:
        """Create generator and player view."""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(16)
        
        # Back button
        back_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Quay lại thư viện")
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self._switch_to_library)
        back_layout.addWidget(self.btn_back)
        back_layout.addStretch()
        layout.addLayout(back_layout)
        
        # Input section
        input_frame = QFrame()
        input_frame.setObjectName("ScriptCard")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setSpacing(12)
        
        input_layout.addWidget(QLabel("Chủ đề:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("VD: Gọi món ở nhà hàng...")
        input_layout.addWidget(self.topic_input, 1)
        
        input_layout.addWidget(QLabel("Cấp độ:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["N5", "N4", "N3", "N2", "N1"])
        self.level_combo.setCurrentText("N4")
        self.level_combo.setFixedWidth(80)
        input_layout.addWidget(self.level_combo)
        
        self.btn_generate = QPushButton("🤖 Tạo bài tập AI")
        self.btn_generate.setObjectName("ActionBtn")
        self.btn_generate.clicked.connect(self._on_generate)
        input_layout.addWidget(self.btn_generate)
        layout.addWidget(input_frame)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #60a5fa; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Script display
        script_scroll = QScrollArea()
        script_scroll.setWidgetResizable(True)
        script_scroll.setStyleSheet("background: transparent; border: none;")
        
        self.script_container = QWidget()
        self.script_layout = QVBoxLayout(self.script_container)
        self.script_layout.setSpacing(12)
        self.script_layout.addStretch()
        script_scroll.setWidget(self.script_container)
        layout.addWidget(script_scroll, 1)
        
        # Audio controls with QMediaPlayer
        controls_frame = QFrame()
        controls_frame.setObjectName("ScriptCard")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(16)
        
        self.btn_play = QPushButton("▶️ Phát")
        self.btn_play.setObjectName("ActionBtn")
        self.btn_play.setFixedWidth(100)
        self.btn_play.clicked.connect(self._on_play_pause)
        self.btn_play.setEnabled(False)
        controls_layout.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton("⏹️ Dừng")
        self.btn_stop.setObjectName("SecondaryBtn")
        self.btn_stop.setFixedWidth(100)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.setEnabled(False)
        controls_layout.addWidget(self.btn_stop)
        
        # Seek slider
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.sliderMoved.connect(self._on_seek)
        controls_layout.addWidget(self.seek_slider, 1)
        
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #9ca3af; min-width: 80px;")
        controls_layout.addWidget(self.time_label)
        
        # Speed control
        controls_layout.addWidget(QLabel("Tốc độ:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        self.speed_combo.setFixedWidth(80)
        controls_layout.addWidget(self.speed_combo)
        
        layout.addWidget(controls_frame)
        
        # Save button
        action_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 Lưu vào thư viện")
        self.btn_save.setObjectName("ActionBtn")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_save.setVisible(False)
        action_layout.addWidget(self.btn_save)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        return view
    
    def _switch_to_library(self):
        """Switch to library view."""
        self.player.stop()
        self.stack.setCurrentIndex(self.VIEW_LIBRARY)
        self._load_library()
    
    def _load_library(self):
        """Load saved lessons."""
        self.lessons_list.clear()
        lessons = self.manager.get_lessons()
        
        self.empty_label.setVisible(len(lessons) == 0)
        self.lessons_list.setVisible(len(lessons) > 0)
        
        for lesson in lessons:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, lesson)
            widget = self._create_lesson_item(lesson)
            # Fix: Set explicit size hint to prevent text cutoff
            from PySide6.QtCore import QSize
            item.setSizeHint(QSize(widget.sizeHint().width(), 90))
            self.lessons_list.addItem(item)
            self.lessons_list.setItemWidget(item, widget)
    
    def _create_lesson_item(self, lesson: Dict) -> QWidget:
        """Create lesson list item widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        info = QVBoxLayout()
        topic = QLabel(f"📝 {lesson.get('topic', 'Untitled')}")
        topic.setStyleSheet("font-size: 15px; font-weight: bold; color: white;")
        info.addWidget(topic)
        
        meta = QLabel(f"{lesson.get('level', 'N4')} • {lesson.get('created_at', '')[:10]}")
        meta.setStyleSheet("font-size: 12px; color: #9ca3af;")
        info.addWidget(meta)
        layout.addLayout(info, 1)
        
        btn_delete = QPushButton("🗑️")
        btn_delete.setObjectName("DeleteBtn")
        btn_delete.setFixedSize(32, 32)
        btn_delete.clicked.connect(lambda: self._on_delete(lesson.get('id')))
        layout.addWidget(btn_delete)
        
        return widget
    
    def _on_lesson_clicked(self, item: QListWidgetItem):
        """Load clicked lesson."""
        lesson = item.data(Qt.UserRole)
        if lesson:
            self._load_lesson(lesson)
    
    def _load_lesson(self, lesson: Dict):
        """Load lesson into player."""
        self.current_lesson = lesson
        self.is_new_lesson = False
        
        self.topic_input.setText(lesson.get('topic', ''))
        self.level_combo.setCurrentText(lesson.get('level', 'N4'))
        self._display_script(lesson.get('script_content', {}))
        
        self.current_audio_path = self.manager.get_audio_path(lesson.get('id'))
        self._setup_audio()
        
        self.btn_save.setVisible(False)
        self.stack.setCurrentIndex(self.VIEW_PLAYER)
        self.status_label.setText("")
    
    def _on_new_practice(self):
        """Start new practice."""
        self.current_lesson = None
        self.current_audio_path = None
        self.is_new_lesson = True
        
        self.topic_input.clear()
        self.level_combo.setCurrentText("N4")
        self._clear_script()
        
        self.btn_play.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_save.setVisible(False)
        
        self.stack.setCurrentIndex(self.VIEW_PLAYER)
        self.status_label.setText("")
        self.topic_input.setFocus()
    
    def _on_generate(self):
        """Generate new script."""
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Thiếu chủ đề", "Vui lòng nhập chủ đề.")
            return
        
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("⏳ Đang tạo...")
        self.status_label.setText("🤖 Đang tạo bài tập với AI...")
        
        self.generate_worker = GenerateScriptWorker(topic, self.level_combo.currentText())
        self.generate_worker.finished.connect(self._on_generate_done)
        self.generate_worker.error.connect(self._on_generate_error)
        self.generate_worker.start()
    
    @Slot(dict)
    def _on_generate_done(self, result: Dict):
        """Handle generation complete."""
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("🤖 Tạo bài tập AI")
        
        if result.get('success'):
            script = result.get('script', {})
            self.current_audio_path = result.get('audio_path')
            
            self.current_lesson = {
                'topic': self.topic_input.text().strip(),
                'level': self.level_combo.currentText(),
                'script_content': script
            }
            self.is_new_lesson = True
            
            self._display_script(script)
            self._setup_audio()
            self.btn_save.setVisible(True)
            self.status_label.setText("✅ Tạo bài tập thành công!")
        else:
            self.status_label.setText(f"❌ Lỗi: {result.get('error', 'Unknown')}")
    
    @Slot(str)
    def _on_generate_error(self, error: str):
        """Handle generation error."""
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("🤖 Tạo bài tập AI")
        self.status_label.setText(f"❌ Lỗi: {error}")
    
    def _display_script(self, script: Dict):
        """Display script content."""
        self._clear_script()
        for i, sentence in enumerate(script.get('sentences', []), 1):
            card = self._create_sentence_card(i, sentence)
            self.script_layout.insertWidget(self.script_layout.count() - 1, card)
    
    def _clear_script(self):
        """Clear script display."""
        while self.script_layout.count() > 1:
            item = self.script_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _create_selectable_text(self, text: str, css_style: str) -> QTextBrowser:
        """Create a selectable text browser that looks like a label."""
        browser = QTextBrowser()
        browser.setHtml(text)
        browser.setReadOnly(True)
        browser.setFrameStyle(QFrame.NoFrame)
        browser.setStyleSheet(f"background: transparent; border: none; {css_style}")
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Set text interaction flags
        browser.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        
        # Context menu
        browser.setContextMenuPolicy(Qt.CustomContextMenu)
        browser.customContextMenuRequested.connect(
            lambda pos: self.show_text_context_menu(browser, pos)
        )
        
        # Adjust height to content logic
        browser.document().setTextWidth(600) # Estimate width, layout will handle resize
        doc_height = browser.document().size().height()
        browser.setFixedHeight(int(doc_height + 15))
        
        return browser

    def _create_sentence_card(self, index: int, sentence: Dict) -> QFrame:
        """Create sentence display card."""
        card = QFrame()
        card.setObjectName("ScriptCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(2)
        
        # Japanese Text
        jp_text = f"{index}. {sentence.get('japanese', '')}"
        valid_jp = sentence.get('japanese', '').strip()
        if valid_jp:
            jp = self._create_selectable_text(
                jp_text, 
                "font-size: 18px; font-weight: bold; color: white;"
            )
            layout.addWidget(jp)
        
        # Reading (Furigana/Romaji)
        reading = sentence.get('reading', '')
        if reading:
            r_label = self._create_selectable_text(
                reading, 
                "font-size: 14px; color: #60a5fa;"
            )
            layout.addWidget(r_label)
        
        # Meaning (Translation)
        meaning = sentence.get('meaning', '')
        if meaning:
            m_label = self._create_selectable_text(
                meaning, 
                "font-size: 14px; color: #9ca3af; font-style: italic;"
            )
            layout.addWidget(m_label)
        
        return card
    
    def _setup_audio(self):
        """Setup QMediaPlayer with current audio."""
        if self.current_audio_path and os.path.exists(self.current_audio_path):
            self.player.setSource(QUrl.fromLocalFile(self.current_audio_path))
            self.btn_play.setEnabled(True)
        else:
            self.btn_play.setEnabled(False)
    
    def _on_play_pause(self):
        """Toggle play/pause."""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
    
    def _on_stop(self):
        """Stop playback."""
        self.player.stop()
    
    @Slot(QMediaPlayer.PlaybackState)
    def _on_playback_state_changed(self, state):
        """Handle playback state change."""
        if state == QMediaPlayer.PlayingState:
            self.btn_play.setText("⏸️ Tạm dừng")
            self.btn_stop.setEnabled(True)
        else:
            self.btn_play.setText("▶️ Phát")
            if state == QMediaPlayer.StoppedState:
                self.btn_stop.setEnabled(False)
    
    @Slot(int)
    def _on_position_changed(self, position):
        """Update seek slider position."""
        if not self.seek_slider.isSliderDown():
            duration = self.player.duration()
            if duration > 0:
                self.seek_slider.setValue(int(position * 100 / duration))
        self._update_time_label()
    
    @Slot(int)
    def _on_duration_changed(self, duration):
        """Handle duration change."""
        self._update_time_label()
    
    def _update_time_label(self):
        """Update time display."""
        pos = self.player.position() // 1000
        dur = self.player.duration() // 1000
        self.time_label.setText(f"{pos//60}:{pos%60:02d} / {dur//60}:{dur%60:02d}")
    
    def _on_seek(self, value):
        """Seek to position."""
        duration = self.player.duration()
        if duration > 0:
            self.player.setPosition(int(value * duration / 100))
    
    def _on_speed_changed(self, speed_text: str):
        """Change playback speed."""
        speed = float(speed_text.replace('x', ''))
        self.player.setPlaybackRate(speed)
    
    def _on_save(self):
        """Save lesson to library."""
        if not self.current_lesson:
            return
        
        result = self.manager.save_lesson(
            topic=self.topic_input.text().strip(),
            level=self.level_combo.currentText(),
            script_content=self.current_lesson.get('script_content', {}),
            temp_audio_path=self.current_audio_path
        )
        
        if result:
            self.current_lesson = result
            self.is_new_lesson = False
            self.btn_save.setVisible(False)
            self.status_label.setText("✅ Đã lưu vào thư viện!")
            toast_success("Đã lưu bài tập!")
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể lưu bài tập.")
    
    def _on_delete(self, lesson_id: str):
        """Delete lesson."""
        reply = QMessageBox.question(
            self, "Xác nhận", "Bạn có chắc muốn xóa?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.manager.delete_lesson(lesson_id):
                self._load_library()
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể xóa.")


class PronunciationTestWidget(QWidget):
    """Widget for Pronunciation Testing (original functionality)."""
    
    def __init__(self):
        super().__init__()
        self.speaking_service = get_speaking_service()
        self.is_recording = False
        self.audio_thread = None
        self.temp_audio_file = None
        self.audio_frames = []
        self.audio_stream = None
        self.audio_format = None
        self._check_audio_libraries()
        self._init_ui()
    
    def _check_audio_libraries(self):
        """Check available audio libraries."""
        if HAS_PYAUDIO:
            try:
                p = pyaudio.PyAudio()
                p.terminate()
                self.audio_available = True
                self.audio_library = "pyaudio"
            except:
                self.audio_available = False
                self.audio_library = None
        elif HAS_SOUNDDEVICE:
            try:
                sd.query_devices()
                self.audio_available = True
                self.audio_library = "sounddevice"
            except:
                self.audio_available = False
                self.audio_library = None
        else:
            self.audio_available = False
            self.audio_library = None
    
    def _init_ui(self):
        """Initialize pronunciation test UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(25)
        
        self._apply_styles()
        
        # Language selector
        lang_layout = QHBoxLayout()
        lang_layout.addStretch()
        lang_layout.addWidget(QLabel("Ngôn ngữ:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Tiếng Anh", "Tiếng Nhật"])
        self.lang_combo.setFixedWidth(120)
        lang_layout.addWidget(self.lang_combo)
        main_layout.addLayout(lang_layout)
        
        # Record button
        rec_layout = QVBoxLayout()
        rec_layout.setAlignment(Qt.AlignCenter)
        
        self.record_btn = QPushButton("GHI ÂM")
        self.record_btn.setObjectName("RecordBtn")
        self.record_btn.setFixedSize(80, 80)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.clicked.connect(self._toggle_recording)
        rec_layout.addWidget(self.record_btn)
        
        self.recording_status = QLabel("Bấm để bắt đầu luyện nói")
        self.recording_status.setStyleSheet("font-size: 14px; margin-top: 10px; color: #7f8c8d;")
        self.recording_status.setAlignment(Qt.AlignCenter)
        rec_layout.addWidget(self.recording_status)
        main_layout.addLayout(rec_layout)
        
        # Score cards
        score_layout = QHBoxLayout()
        score_layout.setSpacing(20)
        
        # Pronunciation card
        pron_card = QFrame()
        pron_card.setObjectName("ScoreCard")
        pron_layout = QVBoxLayout(pron_card)
        pron_layout.addWidget(QLabel("PHÁT ÂM (PRONUNCIATION)"))
        self.pronunciation_score = QLabel("0%")
        self.pronunciation_score.setStyleSheet("font-size: 28px; font-weight: bold; color: #3498db;")
        pron_layout.addWidget(self.pronunciation_score)
        score_layout.addWidget(pron_card, 1)
        
        # Fluency card
        fluency_card = QFrame()
        fluency_card.setObjectName("ScoreCard")
        fluency_layout = QVBoxLayout(fluency_card)
        fluency_layout.addWidget(QLabel("ĐỘ TRÔI CHẢY (FLUENCY)"))
        self.fluency_score = QLabel("0%")
        self.fluency_score.setStyleSheet("font-size: 28px; font-weight: bold; color: #3498db;")
        fluency_layout.addWidget(self.fluency_score)
        score_layout.addWidget(fluency_card, 1)
        
        main_layout.addLayout(score_layout)
        
        # Text areas
        text_layout = QHBoxLayout()
        text_layout.setSpacing(20)
        
        # Transcription
        trans_layout = QVBoxLayout()
        trans_layout.addWidget(QLabel("📝 BẢN GHI (TRANSCRIPTION)"))
        self.transcription = QTextEdit()
        self.transcription.setReadOnly(True)
        self.transcription.setPlaceholderText("Lời nói của bạn sẽ hiện ở đây...")
        trans_layout.addWidget(self.transcription)
        text_layout.addLayout(trans_layout, 1)
        
        # Feedback
        feed_layout = QVBoxLayout()
        feed_layout.addWidget(QLabel("💡 NHẬN XÉT CỦA AI"))
        self.feedback = QTextEdit()
        self.feedback.setReadOnly(True)
        self.feedback.setPlaceholderText("AI sẽ đánh giá chi tiết...")
        feed_layout.addWidget(self.feedback)
        text_layout.addLayout(feed_layout, 1)
        
        main_layout.addLayout(text_layout, 1)
    
    def _apply_styles(self):
        """Apply styles."""
        self.setStyleSheet("""
            QPushButton#RecordBtn {
                background-color: #e74c3c; border-radius: 40px;
                border: 4px solid #c0392b; color: white;
                font-weight: bold; font-size: 14px;
            }
            QPushButton#RecordBtn:checked { background-color: #2ecc71; border-color: #27ae60; }
            
            QFrame#ScoreCard {
                background-color: #16213e; border-radius: 12px;
                border: 1px solid #2e2e42; padding: 15px;
            }
            
            QTextEdit {
                background-color: #1a1a2e; border: 1px solid #2e2e42;
                border-radius: 10px; padding: 15px;
                font-size: 15px; color: #e0e0e0;
            }
            
            QComboBox {
                background: #16213e; color: white;
                border: 1px solid #4a4e69; padding: 5px;
            }
        """)
    
    def _toggle_recording(self):
        """Toggle recording."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start recording."""
        if not self.audio_available:
            QMessageBox.warning(self, "Lỗi", "Không thể khởi tạo thiết bị ghi âm.")
            return
        
        try:
            self.audio_frames = []
            if hasattr(self, 'recording_buffer'):
                self.recording_buffer = []
            
            temp_fd, self.temp_audio_file = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            if self.audio_library == "pyaudio":
                self._start_recording_pyaudio()
            elif self.audio_library == "sounddevice":
                self._start_recording_sounddevice()
            
            self.is_recording = True
            self.record_btn.setText("Dừng")
            self.record_btn.setStyleSheet("background-color: #2ecc71; border-color: #27ae60;")
            self.recording_status.setText("● Đang ghi âm...")
            
            self.pronunciation_score.setText("--")
            self.fluency_score.setText("--")
            self.transcription.clear()
            self.feedback.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể ghi âm: {e}")
            self.is_recording = False
    
    def _start_recording_pyaudio(self):
        """Start PyAudio recording."""
        CHUNK, FORMAT, CHANNELS, RATE = 1024, pyaudio.paInt16, 1, 44100
        self.audio_format = {'chunk': CHUNK, 'format': FORMAT, 'channels': CHANNELS, 'rate': RATE}
        
        self.pyaudio_instance = pyaudio.PyAudio()
        self.audio_stream = self.pyaudio_instance.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, frames_per_buffer=CHUNK
        )
        
        def record():
            while self.is_recording:
                try:
                    data = self.audio_stream.read(CHUNK, exception_on_overflow=False)
                    self.audio_frames.append(data)
                except:
                    break
        
        self.audio_thread = threading.Thread(target=record, daemon=True)
        self.audio_thread.start()
    
    def _start_recording_sounddevice(self):
        """Start sounddevice recording."""
        RATE, CHANNELS = 44100, 1
        self.audio_format = {'rate': RATE, 'channels': CHANNELS, 'dtype': np.int16}
        self.recording_buffer = []
        
        def record():
            def callback(indata, frames, time_info, status):
                if self.is_recording:
                    self.recording_buffer.append(indata.copy())
            
            self.sd_stream = sd.InputStream(
                samplerate=RATE, channels=CHANNELS, dtype=np.int16,
                callback=callback, blocksize=int(RATE * 0.1)
            )
            self.sd_stream.start()
            
            while self.is_recording:
                time.sleep(0.1)
            
            self.sd_stream.stop()
            self.sd_stream.close()
        
        self.audio_thread = threading.Thread(target=record, daemon=True)
        self.audio_thread.start()
    
    def _stop_recording(self):
        """Stop recording and score."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)
        
        if self.audio_library == "pyaudio" and self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            if hasattr(self, 'pyaudio_instance'):
                self.pyaudio_instance.terminate()
        
        self.record_btn.setText("GHI ÂM")
        self.record_btn.setStyleSheet("")
        self.recording_status.setText("🔄 Đang xử lý...")
        
        time.sleep(0.2)
        
        has_data = (self.audio_library == "pyaudio" and self.audio_frames) or \
                   (self.audio_library == "sounddevice" and hasattr(self, 'recording_buffer') and self.recording_buffer)
        
        if has_data:
            try:
                if self.audio_library == "pyaudio":
                    self._save_wav_pyaudio()
                else:
                    self._save_wav_sounddevice()
                
                if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                    with open(self.temp_audio_file, 'rb') as f:
                        audio_data = base64.b64encode(f.read()).decode()
                    
                    os.unlink(self.temp_audio_file)
                    lang = "en" if self.lang_combo.currentIndex() == 0 else "jp"
                    
                    async def score():
                        return await self.speaking_service.score_speaking(audio_data, lang)
                    
                    def update(result):
                        self.recording_status.setText("")
                        if "error" in result:
                            self.feedback.setText(f"Lỗi: {result['error']}")
                        else:
                            self._display_results(result)
                    
                    run_async(score, update)
            except Exception as e:
                self.recording_status.setText("")
                self.feedback.setText(f"Lỗi: {e}")
        else:
            self.recording_status.setText("Lỗi: Không có dữ liệu audio")
    
    def _save_wav_pyaudio(self):
        """Save PyAudio recording."""
        wf = wave.open(self.temp_audio_file, 'wb')
        wf.setnchannels(self.audio_format['channels'])
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.audio_format['format']))
        wf.setframerate(self.audio_format['rate'])
        wf.writeframes(b''.join(self.audio_frames))
        wf.close()
    
    def _save_wav_sounddevice(self):
        """Save sounddevice recording."""
        if self.recording_buffer:
            audio_data = np.concatenate(self.recording_buffer, axis=0)
            if audio_data.ndim > 1:
                audio_data = audio_data.flatten()
            
            wf = wave.open(self.temp_audio_file, 'wb')
            wf.setnchannels(self.audio_format['channels'])
            wf.setsampwidth(2)
            wf.setframerate(self.audio_format['rate'])
            wf.writeframes(audio_data.astype(np.int16).tobytes())
            wf.close()
    
    def _display_results(self, result: dict):
        """Display scoring results."""
        self.pronunciation_score.setText(f"{result.get('pronunciation_score', 0):.0%}")
        self.fluency_score.setText(f"{result.get('fluency_score', 0):.0%}")
        self.transcription.setText(result.get('transcription', ''))
        self.feedback.setText("\n".join(result.get('feedback', [])))
