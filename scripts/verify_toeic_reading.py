import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from frontend.ui.tabs.toeic_reading_tab import ToeicReadingTab
from frontend.ui.styles.style_manager import StyleManager

def run():
    app = QApplication(sys.argv)
    
    # Apply theme
    StyleManager.apply_theme(app)
    
    window = ToeicReadingTab()
    window.setWindowTitle("Verify Toeic Reading Tab")
    window.resize(1000, 600)
    window.show()
    
    print("✅ ToeicReadingTab initialized successfully.")
    
    # Test Data Loading
    total_questions = len(window.questions)
    print(f"✅ Loaded {total_questions} questions.")
    
    if total_questions > 0:
        print(f"✅ First question: {window.questions[0]['question']}")
    else:
        print("❌ No questions loaded!")
        
    # Simulate closing after 3 seconds
    # QTimer.singleShot(3000, app.quit) 
    # For now, we just want to see if it crashes on init.
    # We will close it immediately for the test script.
    
    import time
    # Allow event loop to process for a moment
    app.processEvents()
    time.sleep(1)
    
    print("✅ Verification script finished.")
    # In a real environment, we'd keep it open, but for agent automation:
    sys.exit(0)

if __name__ == "__main__":
    run()
