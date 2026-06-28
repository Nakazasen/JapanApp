"""Style Manager for handling themes and stylesheets."""
from pathlib import Path
from PySide6.QtWidgets import QApplication
from frontend.ui.styles.theme import ModernTheme

class StyleManager:
    """Manages application styles and themes."""
    
    @staticmethod
    def load_stylesheet():
        """Load and parse the main stylesheet."""
        # Get path to main.qss
        current_dir = Path(__file__).parent
        qss_path = current_dir / "main.qss"
        
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                qss_content = f.read()
                
            # Get theme variables
            variables = ModernTheme.get_variables()
            
            # Replace placeholders
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                qss_content = qss_content.replace(placeholder, value)
                
            return qss_content
            
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            return ""

    @staticmethod
    def apply_theme(app: QApplication):
        """Apply theme to the application instance."""
        stylesheet = StyleManager.load_stylesheet()
        if stylesheet:
            app.setStyleSheet(stylesheet)
            print("Theme applied successfully")
        else:
            print("Failed to apply theme")
