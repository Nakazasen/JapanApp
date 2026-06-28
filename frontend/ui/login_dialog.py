"""Login dialog for user authentication."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, QSettings

# Use modular AuthService
from frontend.services import get_auth_service
from frontend.ui.mixins.accessibility_mixin import A11yColors, setup_accessible_name, add_focus_indicator
from frontend.ui.styles.theme import ThemeColors

import aiohttp
import json
from pathlib import Path


class LoginDialog(QDialog):
    """Login dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Use modular AuthService
        self.auth_service = get_auth_service()
        self.token = None
        self.user_info = None
        self.setWindowTitle("Đăng nhập")
        self.setMinimumWidth(300)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI with Modern Card Layout."""
        self.setObjectName("LoginDialog")
        self.resize(1000, 700) # Larger size to show off gradient, card remains centered
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # --- Card Container ---
        self.card = QFrame()
        self.card.setObjectName("login_card")
        self.card.setFixedSize(400, 500)
        
        # Add properties for styling if needed, mainly handled by QSS
        
        # Shadow Effect
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.card.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.card)
        
        # --- Card Layout ---
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)
        
        # Logo/Icon Area
        logo_label = QLabel("📚") # Placeholder icon
        logo_label.setAlignment(Qt.AlignCenter)
        font = logo_label.font()
        font.setPointSize(48)
        logo_label.setFont(font)
        card_layout.addWidget(logo_label)
        
        # Title
        title = QLabel("EnglishApp")
        title.setObjectName("login_title")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)
        
        subtitle = QLabel("Welcome Back!")
        subtitle.setObjectName("login_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)
        
        card_layout.addSpacing(10)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(40)
        card_layout.addWidget(self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        card_layout.addWidget(self.password_input)
        
        # Remember me & Forgot Password Row
        row_layout = QHBoxLayout()
        self.remember_checkbox = QCheckBox("Keep me signed in")
        row_layout.addWidget(self.remember_checkbox)
        
        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet("background: transparent; border: none; color: #0D9488; text-align: right;")
        row_layout.addWidget(forgot_btn)
        
        card_layout.addLayout(row_layout)
        
        card_layout.addSpacing(10)
        
        # Login Button
        self.login_btn = QPushButton("Đăng nhập")
        self.login_btn.setProperty("class", "primary") # Primary Teal Button
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._login)
        self.login_btn.setDefault(True)
        card_layout.addWidget(self.login_btn)
        
        # Register Link
        reg_layout = QHBoxLayout()
        reg_layout.setAlignment(Qt.AlignCenter)
        reg_label = QLabel("Don't have an account?")
        reg_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY};")
        reg_layout.addWidget(reg_label)
        
        self.register_btn = QPushButton("Sign up")
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setStyleSheet(f"background: transparent; border: none; color: {ThemeColors.PRIMARY}; font-weight: bold;")
        self.register_btn.clicked.connect(self._show_register)
        reg_layout.addWidget(self.register_btn)
        
        card_layout.addLayout(reg_layout)
        
        card_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.status_label)
        
        # Load saved credentials
        self._load_saved_credentials()
        
        # Set focus and setup accessibility
        self.username_input.setFocus()
        self._setup_accessibility()
    
    def _setup_accessibility(self):
        """Setup accessibility features."""
        # Set accessible names
        setup_accessible_name(self.username_input, "Tên đăng nhập", "Nhập username của bạn")
        setup_accessible_name(self.password_input, "Mật khẩu", "Nhập mật khẩu của bạn")
        setup_accessible_name(self.remember_checkbox, "Ghi nhớ đăng nhập", "Tự động điền thông tin lần sau")
        setup_accessible_name(self.login_btn, "Nút đăng nhập", "Nhấn để đăng nhập vào ứng dụng")
        setup_accessible_name(self.register_btn, "Nút đăng ký", "Nhấn để tạo tài khoản mới")
        
        # Add focus indicators
        add_focus_indicator(self.username_input)
        add_focus_indicator(self.password_input)
        add_focus_indicator(self.login_btn)
        add_focus_indicator(self.register_btn)
    
    def _login(self):
        """Handle login."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            self.status_label.setText("Vui lòng nhập đầy đủ thông tin!")
            self.status_label.setStyleSheet(f"color: {A11yColors.ERROR}; font-weight: bold;")
            return
        
        self.login_btn.setEnabled(False)
        self.status_label.setText("Đang đăng nhập...")
        self.status_label.setStyleSheet(f"color: {A11yColors.INFO};")
        
        # Use helper function to run in thread
        from frontend.utils.async_helpers import run_async
        
        async def login():
            try:
                print(f"[DEBUG] Starting login for user: {username}")
                print(f"[DEBUG] Calling auth_service.login()")
                # auth_service.login is now SYNC (not async), so no await needed
                result = self.auth_service.login(username, password)
                print(f"[DEBUG] Login result: {result}")
                
                return result
            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                print(f"[DEBUG] Login error: {error_msg}")
                return {"error": error_msg}
        
        def update_ui(result):
            print(f"[DEBUG] update_ui called with result: {result}")
            self.login_btn.setEnabled(True)
            if not result:
                print("[DEBUG] No result received")
                self.status_label.setText("Không nhận được phản hồi từ server!")
                self.status_label.setStyleSheet(f"color: {ThemeColors.DANGER};")
            elif "error" in result:
                error_msg = result["error"]
                print(f"[DEBUG] Error in result: {error_msg}")
                # Truncate long error messages
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                self.status_label.setText(f"Lỗi: {error_msg}")
                self.status_label.setStyleSheet(f"color: {ThemeColors.DANGER};")
            elif "token" in result:
                print(f"[DEBUG] Login successful, token: {result['token']}")
                self.token = result["token"]
                self.user_info = {
                    "id": result.get("user_id"),
                    "username": result.get("username")
                }
                
                # Save credentials if "Remember me" is checked
                if self.remember_checkbox.isChecked():
                    self._save_credentials(username, password)
                else:
                    self._clear_saved_credentials()
                
                self.status_label.setText("Đăng nhập thành công!")
                self.status_label.setStyleSheet(f"color: {ThemeColors.SUCCESS};")
                # Close dialog using QTimer to ensure it's called from main thread
                from PySide6.QtCore import QTimer
                print("[DEBUG] Scheduling accept() via QTimer")
                QTimer.singleShot(100, self.accept)
            else:
                print(f"[DEBUG] Unexpected result format: {result}")
                self.status_label.setText("Đăng nhập thất bại!")
                self.status_label.setStyleSheet(f"color: {ThemeColors.DANGER};")
        
        run_async(login, update_ui)
    
    def _show_register(self):
        """Show register dialog."""
        from frontend.ui.register_dialog import RegisterDialog
        register_dialog = RegisterDialog(self)
        if register_dialog.exec():
            # After successful registration, try to login
            self.username_input.setText(register_dialog.username)
            self.password_input.setText(register_dialog.password)
            self._login()
    
    def get_token(self):
        """Get authentication token."""
        return self.token
    
    def get_user_info(self):
        """Get user info."""
        return self.user_info
    
    def _save_credentials(self, username: str, password: str):
        """Save credentials to settings."""
        try:
            settings = QSettings("EnglishApp", "Login")
            settings.setValue("username", username)
            # Note: In production, password should be encrypted
            # For now, storing plain text (not recommended for production)
            settings.setValue("password", password)
            settings.setValue("remember", True)
            settings.sync()
        except Exception as e:
            print(f"[DEBUG] Failed to save credentials: {e}")
    
    def _load_saved_credentials(self):
        """Load saved credentials from settings."""
        try:
            settings = QSettings("EnglishApp", "Login")
            if settings.value("remember", False, type=bool):
                username = settings.value("username", "")
                password = settings.value("password", "")
                if username:
                    self.username_input.setText(username)
                if password:
                    self.password_input.setText(password)
                    self.remember_checkbox.setChecked(True)
        except Exception as e:
            print(f"[DEBUG] Failed to load credentials: {e}")
    
    def _clear_saved_credentials(self):
        """Clear saved credentials."""
        try:
            settings = QSettings("EnglishApp", "Login")
            settings.remove("username")
            settings.remove("password")
            settings.setValue("remember", False)
            settings.sync()
        except Exception as e:
            print(f"[DEBUG] Failed to clear credentials: {e}")

