
"""
AI Chat Widget - Interactive AI Assistant for EnglishApp
========================================================
Adapted from leetcode_mastery for language learning context.
"""

import os
import webbrowser
import markdown
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit,
    QPushButton, QLabel, QFrame, QComboBox, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QBuffer, QIODevice
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QImage, QPixmap
import io
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from frontend.utils.ai_worker import AIWorker


class PasteAwareTextEdit(QTextEdit):
    """TextEdit that handles image pasting."""
    image_pasted = Signal(QImage)
    
    def canInsertFromMimeData(self, source):
        if source.hasImage():
            return True
        return super().canInsertFromMimeData(source)
    
    def insertFromMimeData(self, source):
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage):
                self.image_pasted.emit(image)
                return
        super().insertFromMimeData(source)


class AIChatWidget(QWidget):
    """
    AI Chat interface for EnglishApp.
    """
    
    # Signals
    request_context = Signal()
    request_settings = Signal()
    
    GEMINI_WEB_URL = "https://gemini.google.com/app"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = None # Will be loaded from config
        self.current_worker = None
        self.chat_history = []
        self.current_context = "" # General context (e.g. current lesson)
        self.last_prompt = ""  
        self.pending_image = None # PIL Image
        
        self.setup_ui()
        self.connect_signals()
        self.refresh_model_display()
    
    def setup_ui(self):
        self.setMinimumWidth(250)
        self.setMaximumWidth(450) # Prevent it from taking too much space
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Chat history
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setFont(QFont("Segoe UI", 11))
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #333;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self._show_welcome_message()
        layout.addWidget(self.chat_display, 1)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Input
        input_area = self._create_input_area()
        layout.addWidget(input_area)
        
        # Model info
        self.model_label = QLabel("🤖 Model: Chưa kết nối")
        self.model_label.setStyleSheet("color: #2e7d32; font-size: 10px;")
        layout.addWidget(self.model_label)
        
        self.setStyleSheet("""
            AIChatWidget {
                background-color: #f8f9fa;
                border-left: 1px solid #dee2e6;
            }
        """)
    
    def _create_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 5, 10, 5)
        
        title = QLabel("🤖 AI Assistant")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addStretch()
        
        self.mode_selector = QComboBox()
        self.mode_selector.addItems([
            "🎓 Gia sư",
            "📝 Sửa lỗi",
            "🌐 Dịch",
            "💡 Tra từ"
        ])
        self.mode_selector.setStyleSheet("""
            QComboBox {
                background-color: #eee;
                border-radius: 4px;
                padding: 2px 5px;
                min-width: 90px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.mode_selector)
        
        # Web btn
        self.web_btn = QPushButton("🌐")
        self.web_btn.setFixedSize(28, 28)
        self.web_btn.setToolTip("Mở Gemini Web")
        self.web_btn.clicked.connect(self._open_gemini_web)
        layout.addWidget(self.web_btn)
        
        # Clear btn
        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.clicked.connect(self.clear_chat)
        layout.addWidget(self.clear_btn)
        
        return header
    
    def _create_input_area(self) -> QWidget:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        # Image Preview Area
        self.image_preview_frame = QFrame()
        self.image_preview_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 5px;")
        self.image_preview_frame.setVisible(False)
        preview_layout = QHBoxLayout(self.image_preview_frame)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        self.image_preview_lbl = QLabel()
        self.image_preview_lbl.setFixedHeight(80)
        self.image_preview_lbl.setScaledContents(True)
        preview_layout.addWidget(self.image_preview_lbl)
        
        preview_layout.addStretch()
        
        remove_img_btn = QPushButton("❌")
        remove_img_btn.setFixedSize(20, 20)
        remove_img_btn.setFlat(True)
        remove_img_btn.clicked.connect(self._clear_pending_image)
        preview_layout.addWidget(remove_img_btn)
        
        container_layout.addWidget(self.image_preview_frame)

        # Input Row
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border: 1px solid #e0e0e0; border-radius: 8px;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 5, 5)
        
        self.input_field = PasteAwareTextEdit()
        self.input_field.image_pasted.connect(self._handle_pasted_image)
        self.input_field.setPlaceholderText("Đặt câu hỏi hoặc dán ảnh... (Ctrl+Enter)")
        self.input_field.setMaximumHeight(60)
        self.input_field.setStyleSheet("border: none;")
        layout.addWidget(self.input_field, 1)
        
        self.send_btn = QPushButton("Gửi")
        self.send_btn.setFixedSize(60, 40)
        self.send_btn.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold; border-radius: 4px;")
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)
        
        container_layout.addWidget(frame)
        
        return container
        
    def _handle_pasted_image(self, qimage):
        """Handle image pasted from clipboard."""
        if not HAS_PIL:
            QMessageBox.warning(self, "Lỗi", "Vui lòng cài đặt Pillow để sử dụng tính năng dán ảnh.\npip install Pillow")
            return
            
        # Convert QImage to PIL Image
        try:
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            qimage.save(buffer, "PNG")
            pil_image = Image.open(io.BytesIO(buffer.data().data()))
            
            self.pending_image = pil_image
            
            # Show preview
            pixmap = QPixmap.fromImage(qimage)
            scaled_pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            self.image_preview_lbl.setPixmap(scaled_pixmap)
            self.image_preview_lbl.setFixedWidth(scaled_pixmap.width())
            self.image_preview_frame.setVisible(True)
            
            # Change mode to "Tutor" or "Translation" automatically if suitable?
            # Keeping current mode for now.
        except Exception as e:
            print(f"Error processing pasted image: {e}")

    def _clear_pending_image(self):
        self.pending_image = None
        self.image_preview_frame.setVisible(False)

    def connect_signals(self):
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.input_field)
        shortcut.activated.connect(self.send_message)

    def _show_welcome_message(self):
        welcome = """
        <div style="color: #444; padding: 10px;">
            <h3>🤖 Trợ lý học tập AI</h3>
            <p>Tôi có thể giúp bạn học Tiếng Nhật và Tiếng Anh hiệu quả hơn:</p>
            <ul>
                <li><b>Gia sư:</b> Giải thích các thắc mắc chung</li>
                <li><b>Sửa lỗi:</b> Kiểm tra ngữ pháp câu</li>
                <li><b>Dịch:</b> Dịch câu kèm phân tích</li>
                <li><b>Giải thích:</b> Tra từ chi tiết</li>
            </ul>
        </div>
        """
        self.chat_display.setHtml(welcome)

    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if not message and not self.pending_image:
            return
            
        # If image only, provide default prompt if empty
        if self.pending_image and not message:
            message = "Giải thích hình ảnh này giúp tôi."
        
        self.set_processing(True)
        self._add_user_message(message)
        self.input_field.clear()
        
        # Emit signal to request context if needed (interface with current tab)
        self.request_context.emit()
        
        # Construct prompt based on mode
        mode = self.mode_selector.currentIndex()
        final_prompt = message
        
        # Add context if available
        context_str = f"\n\nNGỮ CẢNH HIỆN TẠI:\n{self.current_context}\n" if self.current_context else ""
        
        from frontend.services.ai_service import get_ai_service
        service = get_ai_service()
        
        if mode == 0: # Tutor
            if self.pending_image:
                 final_prompt = f"Hãy phân tích và giải thích nội dung trong hình ảnh này. NỘI DUNG THÊM: {message}"
            else:
                 final_prompt = f"Bạn là một gia sư ngôn ngữ tận tâm. Hãy trả lời câu hỏi sau bằng tiếng Việt:{context_str}\nCÂU HỎI: {message}"
        elif mode == 1: # Grammar
            final_prompt = service.construct_grammar_check_prompt(message + context_str, "Japanese/English")
        elif mode == 2: # Translation
            final_prompt = service.construct_translation_prompt(message + context_str, "tự động", "tiếng Việt kèm giải thích ngữ pháp")
        elif mode == 3: # Word Explanation
            final_prompt = service.construct_vocabulary_prompt(message if message else self.current_context, "Japanese/English")

        self.last_prompt = final_prompt
        
        # Pass pending_image
        self.current_worker = AIWorker(final_prompt, image=self.pending_image)
        self.current_worker.result_ready.connect(self._on_ai_response)
        self.current_worker.progress_update.connect(self.status_label.setText)
        self.current_worker.start()
        
        # Clear image after sending
        self._clear_pending_image()

    def _on_ai_response(self, text, model, status):
        self.set_processing(False)
        if status == "success":
            self._add_ai_message(text, model)
        elif status == "fallback":
            self._handle_web_fallback()
        else:
            self._add_system_message("❌ Lỗi", text)

    def _handle_web_fallback(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.last_prompt)
        self._add_system_message("⚠️ Hết lượt sử dụng API", "Đã copy nội dung vào bộ nhớ tạm. Đang chuyển sang bản Web...")
        webbrowser.open(self.GEMINI_WEB_URL)

    def set_processing(self, is_processing):
        self.send_btn.setEnabled(not is_processing)
        self.input_field.setEnabled(not is_processing)
        if is_processing: self.status_label.setText("🤖 Đang suy nghĩ...")
        else: self.status_label.setText("")

    def _add_user_message(self, message):
        msg_content = message
        if self.pending_image:
            msg_content = f"<i>[Đã đính kèm hình ảnh]</i><br/>{message}"
        html = f'<div style="text-align: right; color: #0d47a1; margin-bottom: 10px;"><b>Bạn:</b><br/>{msg_content}</div>'
        self._append_html(html)

    def _add_ai_message(self, message, model):
        md_html = markdown.markdown(message, extensions=['fenced_code', 'tables'])
        html = f'<div style="background-color: #f1f8e9; padding: 10px; border-radius: 8px; margin-bottom: 15px;"><b>AI ({model}):</b><br/>{md_html}</div>'
        self._append_html(html)

    def _add_system_message(self, title, message):
        html = f'<div style="text-align: center; color: #d32f2f;"><b>{title}</b><br/>{message}</div>'
        self._append_html(html)

    def _append_html(self, html):
        self.chat_display.append(html)
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_chat(self):
        self._show_welcome_message()
        self.chat_history.clear()

    def _open_gemini_web(self):
        webbrowser.open(self.GEMINI_WEB_URL)

    def refresh_model_display(self):
        try:
            from frontend.services.ai_service import get_config_manager
            config = get_config_manager()
            active = config.active_models
            if active:
                self.model_label.setText(f"🤖 AI Online: {active[0]}")
            else:
                self.model_label.setText("🤖 AI Offline (Cần API Key)")
        except:
            pass
