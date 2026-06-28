import json
import os
from typing import Dict, Any

class UserSettings:
    """
    Manages user preferences and settings persistence.
    Saves to: .brain/preferences.json (or a local config file if preferred)
    """
    
    _instance = None
    _settings: Dict[str, Any] = {}
    
    # Path to the settings file
    SETTINGS_FILE = os.path.join(os.getcwd(), 'user_preferences.json')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSettings, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        """Load settings from JSON file."""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                self._settings = {}
        else:
            self._settings = {}
            # Set defaults
            self._settings['current_language'] = 'en' # Default to English

    def save_settings(self):
        """Save current settings to JSON file."""
        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self._settings[key] = value
        self.save_settings()

    @property
    def current_language(self) -> str:
        return self.get('current_language', 'en')

    @current_language.setter
    def current_language(self, value: str):
        if value in ['en', 'jp']:
            self.set('current_language', value)
