import os
import requests
from PySide6.QtCore import QUrl, QObject, Signal, QStandardPaths
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class AudioService(QObject):
    """Service to handle downloading and playing audio."""
    
    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.player = None
        self._init_player()
        
    def _init_player(self):
        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(1.0)
        except ImportError:
            print("[AudioService] QtMultimedia not available. Audio disabled.")
            self.player = None

    def play_kana(self, parsed_char: str):
        """Play audio for a kana character. Downloads if necessary."""
        if not self.player:
            return

        # Handle mapped characters (e.g. small tsu)
        # For simplicity, we assume char is the kana itself
        
        filename = f"{parsed_char}.mp3"
        # Location: frontend/data/assets/kana/audio/
        cache_dir = os.path.join(os.getcwd(), 'frontend', 'data', 'assets', 'kana', 'audio')
        os.makedirs(cache_dir, exist_ok=True)
        file_path = os.path.join(cache_dir, filename)
        
        if os.path.exists(file_path):
            self._play_file(file_path)
        else:
            self._download_and_play(parsed_char, file_path)

    def _play_file(self, file_path: str):
        print(f"[AudioService] Playing: {file_path}")
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.player.play()

    def _download_and_play(self, char: str, target_path: str):
        """Download from Google TTS (unofficial) as a reliable placeholder."""
        # Note: This is a fallback. ideally we use the open source repo files.
        # But without a direct file list, this is the most reliable "Native" sound.
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={char}&tl=ja&client=tw-ob"
        
        request = QNetworkRequest(QUrl(url))
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._on_download_finished(reply, target_path))

    def _on_download_finished(self, reply, target_path):
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            with open(target_path, 'wb') as f:
                f.write(data.data())
            self._play_file(target_path)
        else:
            print(f"[AudioService] Download failed: {reply.errorString()}")
        reply.deleteLater()
