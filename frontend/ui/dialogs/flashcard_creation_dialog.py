from typing import List, Dict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QLineEdit, QTextEdit, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from frontend.services.flashcard_service import get_flashcard_service
from frontend.ui.styles.theme import ThemeColors

class FlashcardCreationDialog(QDialog):
    """
    Dialog to review and save flashcards extracted from text.
    """
    def __init__(self, vocab_list: List[Dict[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚡ Create Flashcards")
        self.resize(500, 600)
        self.vocab_list = vocab_list
        self.selected_items = []
        self.flashcard_service = get_flashcard_service()
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("Select words to add to your deck:")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # Scroll Area for Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.items_layout = QVBoxLayout(container)
        
        self.check_boxes = []
        
        for item in self.vocab_list:
            word = item.get("word", "")
            definition = item.get("definition", "")
            example = item.get("example", "")
            
            # Item Widget
            item_widget = QWidget()
            item_widget.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 8px; padding: 10px;")
            h_layout = QHBoxLayout(item_widget)
            
            cb = QCheckBox()
            cb.setChecked(True) # Default select all
            self.check_boxes.append((cb, item))
            h_layout.addWidget(cb)
            
            text_layout = QVBoxLayout()
            lbl_word = QLabel(word)
            lbl_word.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
            lbl_def = QLabel(definition)
            lbl_def.setWordWrap(True)
            lbl_ex = QLabel(f"Ex: {example}")
            lbl_ex.setStyleSheet("font-style: italic; color: #555;")
            lbl_ex.setWordWrap(True)
            
            text_layout.addWidget(lbl_word)
            text_layout.addWidget(lbl_def)
            text_layout.addWidget(lbl_ex)
            
            h_layout.addLayout(text_layout)
            self.items_layout.addWidget(item_widget)
            
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save Selected")
        self.btn_save.clicked.connect(self.save_flashcards)
        self.btn_save.setStyleSheet(f"background-color: {ThemeColors.SUCCESS}; color: white; padding: 10px; border-radius: 5px;")
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)

    def save_flashcards(self):
        saved_count = 0
        user_id = 1 # Hardcoded for now
        
        for cb, item in self.check_boxes:
            if cb.isChecked():
                self.flashcard_service.create_flashcard(
                    user_id=user_id,
                    word=item.get("word", ""),
                    definition=item.get("definition", ""),
                    example=item.get("example", "")
                )
                saved_count += 1
        
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Success", f"Saved {saved_count} flashcards!")
        self.accept()
