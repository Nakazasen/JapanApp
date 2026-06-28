from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QTextEdit, QGroupBox, 
    QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from frontend.ui.styles.theme import ThemeColors, Fonts
from frontend.services.content_generator_service import get_content_service
from frontend.utils.async_helpers import AsyncHelper

class ContentGeneratorTab(QWidget):
    """
    Tab for generating TOEIC content using AI.
    Features:
    - Topic Selection
    - Reading Part 5 Generation
    - Listening Part 1 & 2 Generation (with TTS Audio)
    - Save to Database
    """
    def __init__(self):
        super().__init__()
        self.content_service = get_content_service()
        self.async_helper = AsyncHelper(self)
        self.audio_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_player.setAudioOutput(self.audio_output)
        
        # State to hold generated data for saving
        self.last_reading_data = None
        self.last_listening_data = None
        self.current_audio_path = None
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QLabel("🏭 AI Content Factory")
        header.setFont(Fonts.HEADER)
        header.setStyleSheet(f"color: {ThemeColors.PRIMARY};")
        layout.addWidget(header)

        # Controls Section
        controls_frame = QFrame()
        controls_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 10px; padding: 15px;")
        controls_layout = QHBoxLayout(controls_frame)

        controls_layout.addWidget(QLabel("Topic:"))
        self.topic_combo = QComboBox()
        self.topic_combo.addItems(["Business", "Office", "Travel", "Shopping", "Dining", "Technology", "Health", "Housing"])
        self.topic_combo.setMinimumWidth(150)
        controls_layout.addWidget(self.topic_combo)

        # Part 5 Button
        self.btn_gen_reading = QPushButton("Generate Part 5 (Incomplete Sentences)")
        self.btn_gen_reading.setStyleSheet(f"background-color: {ThemeColors.ACCENT}; color: white; padding: 8px 15px; border-radius: 5px;")
        self.btn_gen_reading.clicked.connect(self.generate_reading)
        controls_layout.addWidget(self.btn_gen_reading)

        # Part 1 Button
        self.btn_gen_part1 = QPushButton("Generate Part 1 (Photos)")
        self.btn_gen_part1.setStyleSheet(f"background-color: {ThemeColors.SECONDARY}; color: white; padding: 8px 15px; border-radius: 5px;")
        self.btn_gen_part1.clicked.connect(lambda: self.generate_listening(part=1))
        controls_layout.addWidget(self.btn_gen_part1)

        # Part 2 Button
        self.btn_gen_part2 = QPushButton("Generate Part 2 (Q&A)")
        self.btn_gen_part2.setStyleSheet(f"background-color: {ThemeColors.SECONDARY}; color: white; padding: 8px 15px; border-radius: 5px;")
        self.btn_gen_part2.clicked.connect(lambda: self.generate_listening(part=2))
        controls_layout.addWidget(self.btn_gen_part2)

        controls_layout.addStretch()
        layout.addWidget(controls_frame)

        # Split View for Results
        results_layout = QHBoxLayout()
        
        # --- Reading Result Area ---
        reading_group = QGroupBox("📖 Reading Output (Part 5)")
        r_layout = QVBoxLayout(reading_group)
        
        self.reading_output = QTextEdit()
        self.reading_output.setReadOnly(True) # Read-only for now as we save raw data
        self.reading_output.setPlaceholderText("Generated reading question will appear here...")
        r_layout.addWidget(self.reading_output)
        
        self.btn_save_reading = QPushButton("💾 Save Reading Question")
        self.btn_save_reading.setEnabled(False)
        self.btn_save_reading.clicked.connect(self.save_reading)
        r_layout.addWidget(self.btn_save_reading)
        
        results_layout.addWidget(reading_group)

        # --- Listening Result Area ---
        listening_group = QGroupBox("🎧 Listening Output (Part 1 & 2)")
        l_layout = QVBoxLayout(listening_group)
        
        self.listening_output = QTextEdit()
        self.listening_output.setReadOnly(True)
        self.listening_output.setPlaceholderText("Generated script will appear here...")
        l_layout.addWidget(self.listening_output)
        
        # Audio Controls
        audio_controls = QHBoxLayout()
        self.btn_play = QPushButton("▶ Play Audio")
        self.btn_play.setEnabled(False)
        self.btn_play.clicked.connect(self.play_audio)
        audio_controls.addWidget(self.btn_play)
        l_layout.addLayout(audio_controls)
        
        self.btn_save_listening = QPushButton("💾 Save Listening Question")
        self.btn_save_listening.setEnabled(False)
        self.btn_save_listening.clicked.connect(self.save_listening)
        l_layout.addWidget(self.btn_save_listening)
        
        results_layout.addWidget(listening_group)

        layout.addLayout(results_layout)

    def generate_reading(self):
        topic = self.topic_combo.currentText()
        self.btn_gen_reading.setEnabled(False)
        self.btn_gen_reading.setText("Generating...")
        self.reading_output.clear()
        self.last_reading_data = None
        self.btn_save_reading.setEnabled(False)
        
        self.async_helper.run(
            self.content_service.generate_reading_part5(topic),
            self.on_reading_generated
        )

    def on_reading_generated(self, result):
        self.btn_gen_reading.setEnabled(True)
        self.btn_gen_reading.setText("Generate Part 5 (Incomplete Sentences)")
        
        if result:
            self.last_reading_data = result
            display_text = (
                f"Topic: {result.get('topic')}\n\n"
                f"Question:\n{result.get('question_text')}\n\n"
                f"Options:\n"
                f"(A) {result.get('options', {}).get('A')}\n"
                f"(B) {result.get('options', {}).get('B')}\n"
                f"(C) {result.get('options', {}).get('C')}\n"
                f"(D) {result.get('options', {}).get('D')}\n\n"
                f"Correct Answer: {result.get('correct_answer')}\n"
                f"Explanation: {result.get('explanation')}"
            )
            self.reading_output.setText(display_text)
            self.btn_save_reading.setEnabled(True)
        else:
            self.reading_output.setText("Failed to generate content. Please try again.")

    def save_reading(self):
        if not self.last_reading_data:
            return
            
        self.async_helper.run(
            self.content_service.save_question_to_db(self.last_reading_data),
            self.on_reading_saved
        )

    def on_reading_saved(self, success):
        if success:
            QMessageBox.information(self, "Success", "Reading question saved to database!")
            self.btn_save_reading.setEnabled(False) # Prevent double save
        else:
            QMessageBox.warning(self, "Error", "Failed to save reading question.")

    def generate_listening(self, part: int):
        topic = self.topic_combo.currentText()
        
        # Disable buttons
        self.btn_gen_part1.setEnabled(False)
        self.btn_gen_part2.setEnabled(False)
        self.listening_output.clear()
        self.last_listening_data = None
        self.btn_save_listening.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.current_audio_path = None
        
        status_text = f"Generating Part {part} (Wait for TTS)..."
        if part == 1: self.btn_gen_part1.setText(status_text)
        else: self.btn_gen_part2.setText(status_text)

        async def pipeline():
            if part == 1:
                script_data = await self.content_service.generate_listening_part1_script(topic)
            else:
                script_data = await self.content_service.generate_listening_part2(topic)
                
            if not script_data: return None
            
            # Generate Audio
            import time
            from frontend.services.tts_service import get_tts_service
            tts = get_tts_service()
            filename = f"gen_part{part}_{int(time.time())}.mp3"
            
            # Use script text for TTS
            # For Part 1: Options A, B, C, D
            # For Part 2: Question + A, B, C
            tts_text = script_data.get("script", "")
            audio_path = await tts.generate_audio(tts_text, filename)
            
            # Attach audio path to data for saving
            script_data["audio_path"] = audio_path
            
            return script_data

        self.async_helper.run(
            pipeline(), 
            lambda res: self.on_listening_generated(res, part)
        )

    def on_listening_generated(self, result, part):
        self.btn_gen_part1.setEnabled(True)
        self.btn_gen_part2.setEnabled(True)
        self.btn_gen_part1.setText("Generate Part 1 (Photos)")
        self.btn_gen_part2.setText("Generate Part 2 (Q&A)")

        if result:
            self.last_listening_data = result
            self.current_audio_path = result.get("audio_path")
            
            display_text = (
                f"Part: {result.get('part')}\n"
                f"Topic: {result.get('topic')}\n\n"
                f"Script:\n{result.get('script')}\n\n"
                f"Correct Answer: {result.get('correct_answer')}\n"
                f"Explanation: {result.get('explanation')}"
            )
            self.listening_output.setText(display_text)
            
            if self.current_audio_path:
                self.btn_play.setEnabled(True)
                
            self.btn_save_listening.setEnabled(True)
        else:
            self.listening_output.setText("Failed to generate content.")

    def play_audio(self):
        if self.current_audio_path:
            self.audio_player.setSource(QUrl.fromLocalFile(self.current_audio_path))
            self.audio_player.play()

    def save_listening(self):
        if not self.last_listening_data:
            return
            
        self.async_helper.run(
            self.content_service.save_question_to_db(self.last_listening_data),
            self.on_listening_saved
        )

    def on_listening_saved(self, success):
        if success:
            QMessageBox.information(self, "Success", "Listening question saved to database!")
            self.btn_save_listening.setEnabled(False)
        else:
            QMessageBox.warning(self, "Error", "Failed to save listening question.")
