"""Settings tab."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QCheckBox, QGroupBox, QFileDialog, QMessageBox, QTextEdit, QComboBox,
    QApplication
)
from PySide6.QtCore import Qt
from frontend.ui.styles.theme import ThemeColors
from frontend.ui.styles.style_manager import StyleManager
from frontend.core.config import settings
from dotenv import load_dotenv
import subprocess
import sys
import os
from pathlib import Path


from frontend.ui.widgets.toast_widget import get_toast_manager

class SettingsTab(QWidget):
    """Settings and configuration tab."""
    
    def __init__(self):
        super().__init__()
        self._reload_settings()
        self._init_ui()
    
    def _get_env_value(self, key: str) -> str:
        """Get value from .env file directly."""
        project_root = Path(__file__).parent.parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        if k.strip() == key:
                            return v.strip().strip('"').strip("'")
        return ""
    
    def _reload_settings(self):
        """Reload settings from .env file."""
        # Reload .env file
        project_root = Path(__file__).parent.parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            # Reload settings by re-reading from environment
            import importlib
            import frontend.core.config
            importlib.reload(frontend.core.config)
            global settings
            settings = frontend.core.config.settings
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Gemini AI Config Section (Waterfall Manager)
        gemini_group = QGroupBox("🤖 Gemini AI Config (Waterfall)")
        gemini_layout = QVBoxLayout()
        
        gemini_info = QLabel("Cấu hình Gemini API và quản lý danh sách AI models với Waterfall strategy (tự động chuyển model khi hết quota).")
        gemini_info.setWordWrap(True)
        gemini_layout.addWidget(gemini_info)
        
        gemini_btn_layout = QHBoxLayout()
        self.open_ai_settings_btn = QPushButton("⚙️ Mở AI Settings & Playground")
        self.open_ai_settings_btn.clicked.connect(self._open_ai_settings)
        gemini_btn_layout.addWidget(self.open_ai_settings_btn)
        gemini_btn_layout.addStretch()
        gemini_layout.addLayout(gemini_btn_layout)
        
        gemini_group.setLayout(gemini_layout)
        layout.addWidget(gemini_group)
        
        # Database section
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout()
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(QLabel("Database Path:"))
        self.db_path = QLineEdit(settings.db_path)
        db_path_layout.addWidget(self.db_path)
        browse_db = QPushButton("Browse...")
        browse_db.clicked.connect(lambda: self._browse_file(self.db_path, is_file=True))
        db_path_layout.addWidget(browse_db)
        db_layout.addLayout(db_path_layout)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Pomodoro Settings Section
        pomo_group = QGroupBox("🍅 Pomodoro Timer Settings")
        pomo_layout = QVBoxLayout()
        
        from PySide6.QtCore import QSettings
        self.pomo_settings = QSettings("EnglishApp", "Pomodoro")
        
        # Work Duration
        work_layout = QHBoxLayout()
        work_layout.addWidget(QLabel("Thời gian học (phút):"))
        from PySide6.QtWidgets import QSpinBox
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 120)
        self.work_spin.setValue(self.pomo_settings.value("work_duration", 25, type=int))
        work_layout.addWidget(self.work_spin)
        pomo_layout.addLayout(work_layout)
        
        # Short Break
        sb_layout = QHBoxLayout()
        sb_layout.addWidget(QLabel("Nghỉ ngắn (phút):"))
        self.sb_spin = QSpinBox()
        self.sb_spin.setRange(1, 30)
        self.sb_spin.setValue(self.pomo_settings.value("short_break_duration", 5, type=int))
        sb_layout.addWidget(self.sb_spin)
        pomo_layout.addLayout(sb_layout)
        
        # Long Break
        lb_layout = QHBoxLayout()
        lb_layout.addWidget(QLabel("Nghỉ dài (phút):"))
        self.lb_spin = QSpinBox()
        self.lb_spin.setRange(1, 60)
        self.lb_spin.setValue(self.pomo_settings.value("long_break_duration", 15, type=int))
        lb_layout.addWidget(self.lb_spin)
        pomo_layout.addLayout(lb_layout)
        
        pomo_group.setLayout(pomo_layout)
        layout.addWidget(pomo_group)
        
        # Accessibility Settings Section (Enterprise)
        a11y_group = QGroupBox("♿ Accessibility Settings")
        a11y_layout = QVBoxLayout()
        
        # High Contrast Mode toggle
        from frontend.ui.mixins.accessibility_mixin import get_high_contrast_manager
        self.hc_manager = get_high_contrast_manager()
        
        hc_layout = QHBoxLayout()
        hc_label = QLabel("High Contrast Mode:")
        hc_label.setToolTip("Bật chế độ độ tương phản cao cho người khiếm thị")
        hc_layout.addWidget(hc_label)
        
        self.high_contrast_checkbox = QCheckBox("Bật")
        self.high_contrast_checkbox.setChecked(self.hc_manager.is_enabled())
        self.high_contrast_checkbox.stateChanged.connect(self._on_high_contrast_changed)
        hc_layout.addWidget(self.high_contrast_checkbox)
        hc_layout.addStretch()
        a11y_layout.addLayout(hc_layout)
        
        a11y_note = QLabel("⚠️ Thay đổi High Contrast Mode cần khởi động lại ứng dụng để có hiệu lực hoàn toàn.")
        a11y_note.setStyleSheet(f"color: {ThemeColors.ACCENT}; font-size: 11px; font-style: italic;")
        a11y_note.setWordWrap(True)
        a11y_layout.addWidget(a11y_note)
        
        a11y_group.setLayout(a11y_layout)
        a11y_group.setLayout(a11y_layout)
        layout.addWidget(a11y_group)

        # Theme Settings Section
        theme_group = QGroupBox("🎨 Theme Settings")
        theme_layout = QHBoxLayout()
        
        theme_layout.addWidget(QLabel("Giao diện:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("🌙 Dark Mode", "dark")
        self.theme_combo.addItem("☀️ Light Mode", "light")
        # Default to dark for now, or load from config if persisted
        self.theme_combo.setCurrentIndex(0) 
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        
        # Actions
        action_layout = QHBoxLayout()
        self.reload_btn = QPushButton("Tải lại cài đặt")
        self.reload_btn.clicked.connect(self._reload_and_refresh)
        action_layout.addWidget(self.reload_btn)
        
        self.save_btn = QPushButton("Lưu cài đặt")
        self.save_btn.clicked.connect(self._save_settings)
        action_layout.addWidget(self.save_btn)
        
        self.clear_cache_btn = QPushButton("Xóa cache")
        self.clear_cache_btn.clicked.connect(self._clear_cache)
        action_layout.addWidget(self.clear_cache_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        layout.addStretch()
    
    def _browse_file(self, line_edit: QLineEdit, is_file: bool = False):
        """Browse for file or directory."""
        if is_file:
            path, _ = QFileDialog.getOpenFileName(
                self, 
                "Chọn file model",
                str(Path(settings.ai_models_path)),
                "GGUF Files (*.gguf);;All Files (*)"
            )
        else:
            path = QFileDialog.getExistingDirectory(self, "Chọn thư mục")
        
        if path:
            line_edit.setText(path)
    
    
    
    def _reload_and_refresh(self):
        """Reload settings from .env and refresh UI."""
        self._reload_settings()
        db_path_value = self._get_env_value("DB_PATH") or settings.db_path
        self.db_path.setText(db_path_value)
        
        get_toast_manager().show_info("Đã tải lại cài đặt từ file .env")
    
    def _save_settings(self):
        """Save settings to .env file."""
        try:
            project_root = Path(__file__).parent.parent.parent.parent
            env_file = project_root / ".env"
            
            # Read existing .env file
            env_vars = {}
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            
            env_vars['DB_PATH'] = self.db_path.text().strip()
            
            # Write back to .env file
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("# English App Configuration\n")
                f.write("# Auto-generated by Settings Tab\n\n")
                
                # Write paths section
                f.write("# Paths\n")
                if 'PROJECT_ROOT' in env_vars:
                    f.write(f"PROJECT_ROOT={env_vars['PROJECT_ROOT']}\n")
                if 'AI_MODELS_PATH' in env_vars:
                    f.write(f"AI_MODELS_PATH={env_vars['AI_MODELS_PATH']}\n")
                if 'PHI3_MODEL_PATH' in env_vars:
                    f.write(f"PHI3_MODEL_PATH={env_vars['PHI3_MODEL_PATH']}\n")
                if 'DB_PATH' in env_vars:
                    f.write(f"DB_PATH={env_vars['DB_PATH']}\n")
                
                f.write("\n# Backend\n")
                if 'BACKEND_HOST' in env_vars:
                    f.write(f"BACKEND_HOST={env_vars['BACKEND_HOST']}\n")
                if 'BACKEND_PORT' in env_vars:
                    f.write(f"BACKEND_PORT={env_vars['BACKEND_PORT']}\n")
                
            
            # Reload settings
            self._reload_settings()
            
            # Save Pomodoro Settings
            self.pomo_settings.setValue("work_duration", self.work_spin.value())
            self.pomo_settings.setValue("short_break_duration", self.sb_spin.value())
            self.pomo_settings.setValue("long_break_duration", self.lb_spin.value())
            
            # Notify main window to refresh pomodoro widget if it exists
            parent_window = self.window()
            if hasattr(parent_window, 'pomodoro_widget'):
                parent_window.pomodoro_widget.reload_settings()
            
            get_toast_manager().show_success("Đã lưu cài đặt thành công!\nCác thay đổi về Pomodoro sẽ được áp dụng ngay.")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Lỗi",
                f"Không thể lưu cài đặt:\n{str(e)}"
            )
    
    def _clear_cache(self):
        """Clear cache."""
        # TODO: Implement cache clearing
        pass
    
    def _open_ai_settings(self):
        """Open the AI Settings & Playground dialog."""
        from frontend.ui.widgets.ai_settings_widget import AISettingsWidget
        dialog = AISettingsWidget(self)
        dialog.exec()
    
    def _on_high_contrast_changed(self, state):
        """Handle high contrast mode toggle."""
        enabled = state == Qt.Checked.value if hasattr(Qt.Checked, 'value') else state == 2
        self.hc_manager.set_enabled(enabled)
        
        # Show toast notification
        from frontend.ui.widgets.toast_widget import get_toast_manager
        toast = get_toast_manager()
        
        if enabled:
            toast.show_info(
                "High Contrast Mode đã bật. Khởi động lại ứng dụng để áp dụng hoàn toàn.",
                action_text="OK"
            )
        else:
            toast.show_info("High Contrast Mode đã tắt.")
            
    def _on_theme_changed(self, index):
        """Handle theme change."""
        mode = self.theme_combo.itemData(index)
        ThemeColors.set_theme(mode)
        
        # Apply strict to app
        app = QApplication.instance()
        if app:
            StyleManager.apply_theme(app)
            
        get_toast_manager().show_info(f"Đã chuyển sang giao diện {mode.title()}")
