"""Shadowing Lesson Manager - Persistence Layer.

Handles saving, loading, and managing shadowing lessons with JSON storage
and audio file caching for offline practice.
"""
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class ShadowingManager:
    """Manages shadowing lesson persistence.
    
    Handles JSON data storage and audio file caching for shadowing lessons.
    Supports save, load, and delete operations with proper file management.
    """
    
    def __init__(self, data_root: Optional[Path] = None):
        """Initialize the ShadowingManager.
        
        Args:
            data_root: Root directory for data storage. Defaults to app's data directory.
        """
        if data_root is None:
            # Default to app's data/user_data directory
            app_root = Path(__file__).parent.parent.parent
            data_root = app_root / "data" / "user_data"
        
        self.data_root = Path(data_root)
        self.data_file = self.data_root / "shadowing_data.json"
        self.audio_cache_dir = self.data_root / "shadowing_audio_cache"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load existing data
        self._data: Dict[str, Any] = self._load_data()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_data(self) -> Dict[str, Any]:
        """Load lesson data from JSON file.
        
        Returns:
            Dictionary containing lessons data.
        """
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure 'lessons' key exists
                    if 'lessons' not in data:
                        data['lessons'] = []
                    return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING ShadowingManager] Failed to load data: {e}")
                return {'lessons': []}
        return {'lessons': []}
    
    def _save_data(self) -> bool:
        """Save lesson data to JSON file.
        
        Returns:
            True if save was successful, False otherwise.
        """
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"[ERROR ShadowingManager] Failed to save data: {e}")
            return False
    
    def save_lesson(
        self,
        topic: str,
        level: str,
        script_content: Dict[str, Any],
        temp_audio_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Save a new shadowing lesson.
        
        Args:
            topic: Lesson topic/title.
            level: JLPT level (N5-N1).
            script_content: Dictionary containing the shadowing script data.
            temp_audio_path: Path to temporary audio file to be cached.
            
        Returns:
            The saved lesson object, or None if save failed.
        """
        try:
            # Generate unique ID
            lesson_id = str(uuid.uuid4())
            
            # Handle audio file
            audio_filename: Optional[str] = None
            if temp_audio_path and os.path.exists(temp_audio_path):
                audio_filename = f"{lesson_id}.mp3"
                dest_path = self.audio_cache_dir / audio_filename
                shutil.copy2(temp_audio_path, dest_path)
                print(f"[INFO ShadowingManager] Audio cached: {dest_path}")
            
            # Create lesson object
            lesson = {
                'id': lesson_id,
                'topic': topic,
                'level': level,
                'created_at': datetime.now().isoformat(),
                'script_content': script_content,
                'audio_filename': audio_filename
            }
            
            # Add to lessons list
            self._data['lessons'].append(lesson)
            
            # Save to file
            if self._save_data():
                print(f"[INFO ShadowingManager] Lesson saved: {topic}")
                return lesson
            else:
                # Rollback: remove the lesson from memory
                self._data['lessons'].remove(lesson)
                # Also remove cached audio if it was copied
                if audio_filename:
                    cached_path = self.audio_cache_dir / audio_filename
                    if cached_path.exists():
                        cached_path.unlink()
                return None
                
        except Exception as e:
            print(f"[ERROR ShadowingManager] Failed to save lesson: {e}")
            return None
    
    def get_lessons(self) -> List[Dict[str, Any]]:
        """Get all lessons sorted by creation date (newest first).
        
        Returns:
            List of lesson dictionaries sorted by date.
        """
        lessons = self._data.get('lessons', [])
        # Sort by created_at descending (newest first)
        return sorted(
            lessons,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
    
    def get_lesson_by_id(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific lesson by its ID.
        
        Args:
            lesson_id: The unique lesson identifier.
            
        Returns:
            Lesson dictionary if found, None otherwise.
        """
        for lesson in self._data.get('lessons', []):
            if lesson.get('id') == lesson_id:
                return lesson
        return None
    
    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete a lesson and its associated audio file.
        
        Args:
            lesson_id: The unique lesson identifier to delete.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            lessons = self._data.get('lessons', [])
            
            # Find the lesson
            lesson_to_delete = None
            for lesson in lessons:
                if lesson.get('id') == lesson_id:
                    lesson_to_delete = lesson
                    break
            
            if not lesson_to_delete:
                print(f"[WARNING ShadowingManager] Lesson not found: {lesson_id}")
                return False
            
            # Delete audio file if exists
            audio_filename = lesson_to_delete.get('audio_filename')
            if audio_filename:
                audio_path = self.audio_cache_dir / audio_filename
                if audio_path.exists():
                    audio_path.unlink()
                    print(f"[INFO ShadowingManager] Audio deleted: {audio_path}")
            
            # Remove from list
            self._data['lessons'].remove(lesson_to_delete)
            
            # Save changes
            if self._save_data():
                print(f"[INFO ShadowingManager] Lesson deleted: {lesson_id}")
                return True
            else:
                # Rollback: add the lesson back
                self._data['lessons'].append(lesson_to_delete)
                return False
                
        except Exception as e:
            print(f"[ERROR ShadowingManager] Failed to delete lesson: {e}")
            return False
    
    def get_audio_path(self, lesson_id: str) -> Optional[str]:
        """Get the audio file path for a lesson.
        
        Args:
            lesson_id: The unique lesson identifier.
            
        Returns:
            Absolute path to audio file if exists, None otherwise.
        """
        lesson = self.get_lesson_by_id(lesson_id)
        if not lesson:
            return None
        
        audio_filename = lesson.get('audio_filename')
        if not audio_filename:
            return None
        
        audio_path = self.audio_cache_dir / audio_filename
        if audio_path.exists():
            return str(audio_path)
        
        print(f"[WARNING ShadowingManager] Audio file missing: {audio_path}")
        return None
    
    def update_lesson(self, lesson_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing lesson.
        
        Args:
            lesson_id: The unique lesson identifier.
            updates: Dictionary of fields to update.
            
        Returns:
            True if update was successful, False otherwise.
        """
        lesson = self.get_lesson_by_id(lesson_id)
        if not lesson:
            return False
        
        # Update allowed fields
        allowed_fields = ['topic', 'level', 'script_content']
        for field in allowed_fields:
            if field in updates:
                lesson[field] = updates[field]
        
        return self._save_data()
    
    def get_lesson_count(self) -> int:
        """Get total number of saved lessons.
        
        Returns:
            Number of lessons in the library.
        """
        return len(self._data.get('lessons', []))


# Singleton instance
_shadowing_manager: Optional[ShadowingManager] = None


def get_shadowing_manager() -> ShadowingManager:
    """Get global ShadowingManager instance.
    
    Returns:
        Singleton ShadowingManager instance.
    """
    global _shadowing_manager
    if _shadowing_manager is None:
        _shadowing_manager = ShadowingManager()
    return _shadowing_manager
