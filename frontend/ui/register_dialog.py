"""Register dialog for new user registration."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from frontend.ui.styles.theme import ThemeColors
from frontend.services import get_auth_service
from frontend.utils.async_helpers import run_async


class RegisterDialog(QDialog):
    """Register dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = get_auth_service()
        self.username = None
        self.password = None
        self.setWindowTitle("Đăng ký")
        self.setMinimumWidth(300)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Đăng ký tài khoản mới")
        title.setAlignment(Qt.AlignCenter)
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Username
        layout.addWidget(QLabel("Tên đăng nhập:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nhập username...")
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Mật khẩu:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nhập mật khẩu...")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # Confirm Password
        layout.addWidget(QLabel("Xác nhận mật khẩu:"))
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Nhập lại mật khẩu...")
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_confirm_input)
        
        # Email (optional)
        layout.addWidget(QLabel("Email (tùy chọn):"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Nhập email...")
        layout.addWidget(self.email_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.register_btn = QPushButton("Đăng ký")
        self.register_btn.clicked.connect(self._register)
        self.register_btn.setDefault(True)
        button_layout.addWidget(self.register_btn)
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Set focus
        self.username_input.setFocus()
    
    def _register(self):
        """Handle registration."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        password_confirm = self.password_confirm_input.text().strip()
        email = self.email_input.text().strip() or None
        
        if not username or not password:
            self.status_label.setText("Vui lòng nhập đầy đủ thông tin!")
            self.status_label.setStyleSheet(f"color: {ThemeColors.DANGER};")
            return
        
        if password != password_confirm:
            self.status_label.setText("Mật khẩu xác nhận không khớp!")
            self.status_label.setStyleSheet(f"color: {ThemeColors.DANGER};")
            return
        
        self.register_btn.setEnabled(False)
        self.status_label.setText("Đang đăng ký...")
        self.status_label.setStyleSheet(f"color: {ThemeColors.PRIMARY};")
        
        async def register():
            try:
                # AuthService.register is synchronous
                result = self.auth_service.register(username, password, email)
                return result
            except Exception as e:
                return {"error": str(e)}
        
        def update_ui(result):
            self.register_btn.setEnabled(True)
            if "error" in result:
                self.status_label.setText(f"Lỗi: {result['error']}")
                self.status_label.setStyleSheet(f"color: {ThemeColors.DANGER};")
            else:
                self.username = username
                self.password = password
                self.status_label.setText("Đăng ký thành công!")
                self.status_label.setStyleSheet(f"color: {ThemeColors.SUCCESS};")
                QMessageBox.information(self, "Thành công", "Đăng ký thành công! Bạn sẽ được đăng nhập tự động.")
                self.accept()  # Close dialog with success
        
        run_async(register, update_ui)

