"""Frontend application entry point."""
import sys
from pathlib import Path

# Add project root to path if not already there
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox
from frontend.ui.main_window import MainWindow
from frontend.ui.login_dialog import LoginDialog
from frontend.ui.styles.style_manager import StyleManager


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Ứng dụng học Tiếng Anh & Tiếng Nhật")
    
    # Apply theme globally before showing any UI
    StyleManager.apply_theme(app)
    
    # Show login dialog first
    login_dialog = LoginDialog()
    result = login_dialog.exec()
    print(f"[DEBUG main] Login dialog result: {result}")
    if result != 1:  # QDialog.Accepted = 1
        # User cancelled login
        print("[DEBUG main] Login cancelled or failed")
        sys.exit(0)
    
    # Get token and user info
    token = login_dialog.get_token()
    user_info = login_dialog.get_user_info()
    
    print(f"[DEBUG main] Token: {token}")
    print(f"[DEBUG main] User info: {user_info}")
    
    if not token:
        QMessageBox.critical(None, "Lỗi", "Không thể đăng nhập. Vui lòng thử lại.")
        sys.exit(1)
    
    # Backend connection check removed (Backend-less)
    print("[Main] Backend-less mode active.")
    
    # Show main window
    window = MainWindow()
    window.setWindowTitle(f"Ứng dụng học Tiếng Anh & Tiếng Nhật - {user_info.get('username', 'User') if user_info else 'User'}")
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

