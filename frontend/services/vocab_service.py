"""Vocabulary Service - Local database operations (no HTTP backend).

This service manages:
- Vocabulary CRUD (Create, Read, Update, Delete) via SQLite
- Search and lookup
- SRS (Spaced Repetition) review functionality
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select, or_, col, func

from frontend.services.base_service import BaseService, ServiceError
from frontend.core.database import get_session
from frontend.models.vocab import JpVocabItem, EnVocabItem, MasteryStatus, VocabTopic
from frontend.models.unified_vocab import VocabItem
from frontend.models.study import StudyHistory
from frontend.services.srs_service import SRSService


class VocabService(BaseService):
    """Service for vocabulary-related database operations.
    
    Uses SQLite directly instead of HTTP backend.
    """
    
    def _get_model(self, lang: str, use_unified: bool = True):
        """Get appropriate model for language.
        
        Args:
            lang: Language code ("en", "jp", "kr", etc.)
            use_unified: If True, returns the new VocabItem model. 
                         If False, returns legacy JpVocabItem/EnVocabItem for backward compat.
        """
        if use_unified:
            return VocabItem
        # Legacy fallback
        return JpVocabItem if lang == "jp" else EnVocabItem
    
    # =============== Topic Management ===============
    
    def create_topic(self, name: str, lang: str, description: str = None) -> Dict[str, Any]:
        """Create a new vocabulary topic/deck."""
        try:
            with get_session() as session:
                topic = VocabTopic(
                    user_id=self.get_current_user_id(),
                    name=name,
                    lang=lang,
                    description=description
                )
                session.add(topic)
                session.commit()
                session.refresh(topic)
                return {"success": True, "id": topic.id, "name": topic.name}
        except Exception as e:
            return {"error": str(e)}

    def list_topics(self, lang: str) -> List[Dict[str, Any]]:
        """List all topics for a language."""
        try:
            with get_session() as session:
                statement = select(VocabTopic).where(
                    VocabTopic.user_id == self.get_current_user_id(),
                    VocabTopic.lang == lang
                )
                topics = session.exec(statement).all()
                return [
                    {"id": t.id, "name": t.name, "description": t.description} 
                    for t in topics
                ]
        except Exception as e:
            print(f"[VocabService] list_topics error: {e}")
            return []
    
    # =============== Basic CRUD ===============
    
    def search(self, word: str, lang: str) -> Dict[str, Any]:
        """Search vocabulary in local database.
        
        Args:
            word: Word to search
            lang: Language ("en" or "jp")
            
        Returns:
            Search result with meaning and metadata
        """
        try:
            Model = self._get_model(lang)
            
            with get_session() as session:
                # Search by word or reading
                if lang == "jp":
                    statement = select(Model).where(
                        or_(
                            Model.word == word,
                            Model.reading == word
                        )
                    )
                else:
                    statement = select(Model).where(Model.word == word)
                
                item = session.exec(statement).first()
                
                if item:
                    return {
                        "found": True,
                        "id": item.id,
                        "word": item.word,
                        "meaning": item.meaning,
                        "reading": getattr(item, 'reading', None),
                        "mastery_status": item.mastery_status,
                        "user_note": item.user_note
                    }
                
                return {"found": False, "word": word}
                
        except Exception as e:
            return {"error": str(e)}
    
    def save(self, vocab_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save new vocabulary item to unified table.
        
        Args:
            vocab_data: Vocabulary data including lang, word/term, meaning, etc.
            
        Returns:
            Result with new vocabulary ID
        """
        try:
            lang = vocab_data.get("lang", "en")
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            
            # Normalize field names: accept both 'word' and 'term'
            term = vocab_data.get("term") or vocab_data.get("word", "")
            
            with get_session() as session:
                # Check if word exists in unified table
                existing = session.exec(
                    select(Model).where(
                        Model.term == term,
                        Model.lang == lang,
                        Model.user_id == user_id
                    )
                ).first()
                
                if existing:
                    return {"error": "Từ vựng này đã tồn tại"}
                
                # Build examples list from various input formats
                examples = vocab_data.get("examples", [])
                if isinstance(examples, str) and examples:
                    examples = [{"sentence": examples, "translation": ""}]
                elif vocab_data.get("example"):
                    examples = [{"sentence": vocab_data["example"], "translation": ""}]
                
                # Build meta_data from language-specific fields
                meta_data = vocab_data.get("meta_data", {})
                if vocab_data.get("han_viet"):
                    meta_data["han_viet"] = vocab_data["han_viet"]
                if vocab_data.get("romaji"):
                    meta_data["romaji"] = vocab_data["romaji"]
                if vocab_data.get("ipa"):
                    meta_data["ipa"] = vocab_data["ipa"]
                if vocab_data.get("pos"):
                    meta_data["pos"] = vocab_data["pos"]
                
                # Create new item using unified model
                item = Model(
                    user_id=user_id,
                    term=term,
                    reading=vocab_data.get("reading", ""),
                    meaning=vocab_data.get("meaning", ""),
                    lang=lang,
                    level=vocab_data.get("level", ""),
                    source_material=vocab_data.get("source_material", ""),
                    topic_id=vocab_data.get("topic_id"),
                    meta_data=meta_data,
                    examples=examples,
                    user_note=vocab_data.get("user_note", ""),
                    tags=vocab_data.get("tags", ""),
                    mastery_status=MasteryStatus.NEW.value,
                    created_at=datetime.utcnow()
                )
                session.add(item)
                session.commit()
                session.refresh(item)
                
                return {"success": True, "id": item.id}
                
        except Exception as e:
            print(f"[VocabService] save error: {e}")
            return {"error": str(e)}
    
    def save_jp_vocab(self, vocab_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save new Japanese vocabulary item using unified model.
        
        Args:
            vocab_data: Dict with word_kanji, word_kana, meaning_vi, example_jp, topic_id, source_material
            
        Returns:
            Result with new vocabulary ID or error
        """
        # Map Japanese-specific fields to unified format
        unified_data = {
            "lang": "jp",
            "term": vocab_data.get("word_kanji", ""),
            "reading": vocab_data.get("word_kana", ""),
            "meaning": vocab_data.get("meaning_vi", ""),
            "level": vocab_data.get("level", ""),
            "source_material": vocab_data.get("source_material", ""),
            "topic_id": vocab_data.get("topic_id"),
            "user_note": vocab_data.get("user_note", ""),
            "meta_data": {
                "han_viet": vocab_data.get("han_viet", ""),
                "romaji": vocab_data.get("romaji", ""),
            },
            "examples": []
        }
        
        # Add examples if present
        if vocab_data.get("example_jp"):
            unified_data["examples"].append({
                "sentence": vocab_data["example_jp"],
                "translation": vocab_data.get("example_vi", "")
            })
        
        return self.save(unified_data)
    
    def add_vocab(self, vocab_data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Add new vocabulary item (wrapper for save with explicit lang).
        
        Args:
            vocab_data: Vocabulary data dict (word, meaning, reading, examples, etc.)
            lang: Language ("en" or "jp")
            
        Returns:
            Result with success or error
        """
        vocab_data["lang"] = lang
        # Map 'examples' to 'example' field if present
        if "examples" in vocab_data and "example" not in vocab_data:
            vocab_data["example"] = vocab_data.pop("examples")
        return self.save(vocab_data)
    
    def delete_vocab(self, vocab_id: int, lang: str) -> Dict[str, Any]:
        """Delete vocabulary item (alias for delete).
        
        Args:
            vocab_id: ID of vocabulary to delete
            lang: Language ("en" or "jp")
            
        Returns:
            Result with success or error
        """
        return self.delete(vocab_id, lang)
    
    def list_all(self, lang: str) -> List[Dict[str, Any]]:
        """Get all saved vocabulary for a language.
        
        Args:
            lang: Language ("en" or "jp", "kr", etc.)
            
        Returns:
            List of vocabulary items
        """
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            
            with get_session() as session:
                statement = select(Model).where(
                    Model.user_id == user_id,
                    Model.lang == lang  # Filter by language for unified table
                )
                items = session.exec(statement).all()
                
                return [
                    {
                        "id": item.id,
                        "word": item.term,  # Use unified field name
                        "meaning": item.meaning,
                        "reading": item.reading,
                        "level": item.level,
                        "mastery_status": item.mastery_status,
                        "srs_level": item.srs_level,
                        "next_review": str(item.next_review) if item.next_review else None,
                        "created_at": str(item.created_at),
                        # Language-specific metadata from meta_data JSON
                        "han_viet": item.meta_data.get("han_viet") if item.meta_data else None,
                        "romaji": item.meta_data.get("romaji") if item.meta_data else None,
                        "ipa": item.meta_data.get("ipa") if item.meta_data else None,
                    }
                    for item in items
                ]
                
        except Exception as e:
            print(f"[VocabService] list_all error: {e}")
            return []
    
    def delete(self, vocab_id: int, lang: str) -> Dict[str, Any]:
        """Delete a vocabulary item.
        
        Args:
            vocab_id: ID of vocabulary to delete
            lang: Language ("en" or "jp")
            
        Returns:
            Deletion confirmation
        """
        try:
            Model = self._get_model(lang)
            
            with get_session() as session:
                item = session.get(Model, vocab_id)
                if item:
                    session.delete(item)
                    session.commit()
                    return {"success": True}
                return {"error": "Không tìm thấy từ vựng"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def update_note(self, vocab_id: int, user_note: str, lang: str) -> Dict[str, Any]:
        """Update vocabulary note.
        
        Args:
            vocab_id: ID of vocabulary
            user_note: New note content
            lang: Language ("en" or "jp")
            
        Returns:
            Update confirmation
        """
        try:
            Model = self._get_model(lang)
            
            with get_session() as session:
                item = session.get(Model, vocab_id)
                if item:
                    item.user_note = user_note
                    session.add(item)
                    session.commit()
                    return {"success": True}
                return {"error": "Không tìm thấy từ vựng"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def update_vocab(self, vocab_id: int, vocab_data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Update vocabulary item with new data using unified model.
        
        Args:
            vocab_id: ID of vocabulary
            vocab_data: Dict with fields to update (word/term, reading, meaning, examples, etc.)
            lang: Language code (for backward compatibility, not used for filtering since ID is unique)
            
        Returns:
            Update confirmation
        """
        try:
            Model = self._get_model(lang)
            
            with get_session() as session:
                item = session.get(Model, vocab_id)
                if item:
                    # Update unified fields
                    if vocab_data.get("word") or vocab_data.get("term"):
                        item.term = vocab_data.get("term") or vocab_data.get("word")
                    if vocab_data.get("reading"):
                        item.reading = vocab_data["reading"]
                    if vocab_data.get("meaning"):
                        item.meaning = vocab_data["meaning"]
                    
                    # Update examples if provided
                    if vocab_data.get("examples"):
                        examples = vocab_data["examples"]
                        if isinstance(examples, str):
                            item.examples = [{"sentence": examples, "translation": ""}]
                        elif isinstance(examples, list):
                            item.examples = examples
                    
                    # Update meta_data (merge with existing)
                    if vocab_data.get("han_viet") or vocab_data.get("romaji") or vocab_data.get("ipa") or vocab_data.get("pos"):
                        meta = item.meta_data or {}
                        if vocab_data.get("han_viet"):
                            meta["han_viet"] = vocab_data["han_viet"]
                        if vocab_data.get("romaji"):
                            meta["romaji"] = vocab_data["romaji"]
                        if vocab_data.get("ipa"):
                            meta["ipa"] = vocab_data["ipa"]
                        if vocab_data.get("pos"):
                            meta["pos"] = vocab_data["pos"]
                        item.meta_data = meta
                    
                    # Common fields
                    if vocab_data.get("user_note") is not None:
                        item.user_note = vocab_data["user_note"]
                    if vocab_data.get("level"):
                        item.level = vocab_data["level"]
                    if vocab_data.get("tags") is not None:
                        item.tags = vocab_data["tags"]
                    if "is_ai_enriched" in vocab_data:
                        item.is_ai_enriched = vocab_data["is_ai_enriched"]
                    
                    session.add(item)
                    session.commit()
                    return {"success": True}
                return {"error": "Không tìm thấy từ vựng"}
                
        except Exception as e:
            print(f"[VocabService] update_vocab error: {e}")
            return {"error": str(e)}
    
    # =============== SRS (Spaced Repetition) ===============
    
    async def get_due(
        self, 
        lang: str, 
        include_new: bool = True, 
        limit: int = 50,
        topic_id: Optional[int] = None,
        source_material: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get vocabulary items due for review (SRS).
        
        Args:
            lang: Language ("en", "jp", "kr", etc.)
            include_new: Include new words that haven't been reviewed
            limit: Maximum number of items to return
            topic_id: Filter by topic ID
            source_material: Filter by curriculum source
            level: Filter by level
            
        Returns:
            List of vocabulary items due for review
        """
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            now = datetime.utcnow()
            
            with get_session() as session:
                # Get items due for review
                conditions = [
                    Model.user_id == user_id,
                    Model.lang == lang,  # Filter by language for unified table
                    or_(
                        Model.next_review <= now,
                        Model.next_review == None
                    ) if include_new else Model.next_review <= now
                ]
                
                if topic_id is not None:
                    conditions.append(Model.topic_id == topic_id)
                if source_material:
                    conditions.append(Model.source_material == source_material)
                if level:
                    conditions.append(Model.level == level)
                
                statement = select(Model).where(*conditions).limit(limit)
                items = session.exec(statement).all()
                
                return [
                    {
                        "id": item.id,
                        "word": item.term,
                        "meaning": item.meaning,
                        "reading": item.reading,
                        "han_viet": item.meta_data.get("han_viet") if item.meta_data else None,
                        "examples": item.examples[0].get("sentence") if item.examples else None,
                        "user_note": item.user_note,
                        "mastery_status": item.mastery_status,
                        "srs_level": item.srs_level
                    }
                    for item in items
                ]
                
        except Exception as e:
            print(f"[VocabService] get_due error: {e}")
            return []
    
    def submit_review(
        self, 
        vocab_id: int, 
        rating: int, 
        lang: str
    ) -> Dict[str, Any]:
        """Submit vocabulary review with SRS rating.
        
        Args:
            vocab_id: ID of vocabulary item
            rating: Rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            lang: Language ("en" or "jp")
            
        Returns:
            Updated SRS data
        """
        try:
            Model = self._get_model(lang)
            
            # SRS logic delegated to SRSService
            
            with get_session() as session:
                item = session.get(Model, vocab_id)
                if not item:
                    return {"error": "Không tìm thấy từ vựng"}
                
                current_streak = getattr(item, 'srs_streak', 0)
                current_ef = getattr(item, 'srs_ease_factor', 2.5)
                current_interval = getattr(item, 'srs_interval', 0)
                
                # Update SRS level based on rating using SRSService
                new_streak, new_ef, new_interval = SRSService.calculate_next_state(
                    current_streak=current_streak,
                    current_ease_factor=current_ef,
                    current_interval=current_interval,
                    quality=rating
                )
                
                item.srs_streak = new_streak
                item.srs_ease_factor = new_ef
                item.srs_interval = new_interval
                item.next_review = SRSService.get_next_review_date(new_interval)
                
                # Update mastery status
                if rating == 1:
                    item.mastery_status = MasteryStatus.HARD.value
                elif new_interval >= 21:
                    item.mastery_status = MasteryStatus.MASTERED.value
                elif new_interval >= 7:
                    item.mastery_status = MasteryStatus.REVIEWING.value
                else:
                    item.mastery_status = MasteryStatus.LEARNING.value
                
                item.review_count = getattr(item, 'review_count', 0) + 1
                item.last_reviewed = datetime.utcnow()
                
                session.add(item)
                
                # Record study history for dashboard/gamification
                from frontend.services.base_service import BaseService
                user_id = BaseService.get_current_user_id()
                
                history = StudyHistory(
                    user_id=user_id,
                    vocab_id=vocab_id,
                    lang=lang,
                    study_date=datetime.utcnow(),
                    words_reviewed=1,
                    status=item.mastery_status
                )
                session.add(history)
                
                session.commit()
                
                return {
                    "success": True,
                    "srs_level": item.srs_level,
                    "next_review": str(item.next_review),
                    "mastery_status": item.mastery_status
                }
                
        except Exception as e:
            return {"error": str(e)}

    async def get_random_review_items(
        self, 
        lang: str, 
        limit: int = 20,
        topic_id: Optional[int] = None,
        source_material: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get random items for review (due or learning) for Tinder mode."""
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            
            with get_session() as session:
                # Prioritize learning/reviewing items, but can include new
                conditions = [
                    Model.user_id == user_id,
                    Model.lang == lang,  # Filter by language for unified table
                    Model.mastery_status != MasteryStatus.MASTERED.value
                ]
                
                # Apply filters
                if topic_id == -1:
                    conditions.append(Model.topic_id == None)
                elif topic_id is not None:
                    conditions.append(Model.topic_id == topic_id)
                
                if source_material:
                    conditions.append(Model.source_material == source_material)
                
                if level:
                    conditions.append(Model.level == level)
                
                statement = select(Model).where(*conditions).order_by(func.random()).limit(limit)
                
                items = session.exec(statement).all()
                return [
                    {
                        "id": item.id,
                        "word": item.term,
                        "meaning": item.meaning,
                        "pronunciation": item.reading,
                        "level": item.level or "N/A",
                        "mastery_status": item.mastery_status,
                        "kanji": item.term if lang == "jp" else None,
                        "examples": item.examples[0].get("sentence") if item.examples else None,
                        "user_note": item.user_note,
                        "han_viet": item.meta_data.get("han_viet") if item.meta_data else None
                    }
                    for item in items
                ]
        except Exception as e:
            print(f"Error fetching random review items: {e}")
            return []
    
    def get_stats(self, lang: str, topic_id: Optional[int] = None, source_material: Optional[str] = None, level: Optional[str] = None) -> Dict[str, Any]:
        """Get vocabulary learning statistics with filtering.
        
        Args:
            lang: Language ("en" or "jp")
            topic_id: Filter by topic ID
            source_material: Filter by source
            level: Filter by level
            
        Returns:
            Statistics including total, due, new, learning, mastered counts
        """
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            now = datetime.utcnow()
            
            with get_session() as session:
                conditions = [Model.user_id == user_id, Model.lang == lang]
                if topic_id is not None: conditions.append(Model.topic_id == topic_id)
                if source_material: conditions.append(Model.source_material == source_material)
                if level: conditions.append(Model.level == level)
                
                # Total count
                total = session.exec(
                    select(Model).where(*conditions)
                ).all()
                
                stats = {
                    "total": len(total),
                    "new": 0,
                    "learning": 0,
                    "reviewing": 0,
                    "mastered": 0,
                    "due": 0
                }
                
                for item in total:
                    status = item.mastery_status
                    if status == MasteryStatus.NEW.value:
                        stats["new"] += 1
                    elif status == MasteryStatus.LEARNING.value:
                        stats["learning"] += 1
                    elif status == MasteryStatus.REVIEWING.value:
                        stats["reviewing"] += 1
                    elif status == MasteryStatus.MASTERED.value:
                        stats["mastered"] += 1
                    
                    # Check if due
                    if item.next_review and item.next_review <= now:
                        stats["due"] += 1
                    elif not item.next_review:
                        stats["due"] += 1  # New items are also "due"
                
                return stats
                
        except Exception as e:
            return {"error": str(e), "total": 0}
    
    # =============== Advanced Filtering ===============
    
    def list_by_filters(
        self,
        lang: str,
        topic_id: Optional[int] = None,
        source_material: Optional[str] = None,
        level: Optional[str] = None,
        mastery_statuses: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Lọc từ vựng theo nhiều tiêu chí.
        
        Args:
            lang: Language ("en" or "jp")
            topic_id: Filter by topic/deck ID
            source_material: Filter by curriculum source (e.g., "Soumatome N3")
            level: Filter by level (e.g., "N3", "IELTS 6.5")
            mastery_statuses: List of statuses to include (new, learning, hard, mastered)
            search_query: Search in word/meaning
            limit: Maximum results
            
        Returns:
            List of vocabulary items matching filters
        """
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            
            with get_session() as session:
                # Build query with lang filter for unified table
                conditions = [Model.user_id == user_id, Model.lang == lang]
                
                if topic_id == -1:
                    conditions.append(Model.topic_id == None)
                elif topic_id is not None:
                    conditions.append(Model.topic_id == topic_id)
                
                if source_material:
                    conditions.append(Model.source_material == source_material)
                
                if level:
                    conditions.append(Model.level == level)
                
                if mastery_statuses:
                    conditions.append(Model.mastery_status.in_(mastery_statuses))
                
                if search_query:
                    search_pattern = f"%{search_query}%"
                    # Use unified field names
                    conditions.append(
                        or_(
                            Model.term.like(search_pattern),
                            Model.reading.like(search_pattern),
                            Model.meaning.like(search_pattern)
                        )
                    )
                
                statement = select(Model).where(*conditions).limit(limit)
                items = session.exec(statement).all()
                
                # Convert to dict using unified fields
                results = []
                for item in items:
                    results.append({
                        "id": item.id,
                        "word": item.term,
                        "reading": item.reading,
                        "meaning": item.meaning,
                        "han_viet": item.meta_data.get("han_viet") if item.meta_data else None,
                        "examples": item.examples[0].get("sentence") if item.examples else None,
                        "user_note": item.user_note,
                        "level": item.level,
                        "source_material": item.source_material,
                        "mastery_status": item.mastery_status,
                        "topic_id": item.topic_id,
                        "tags": item.tags,
                        "is_ai_enriched": item.is_ai_enriched,
                        "created_at": str(item.created_at) if item.created_at else None
                    })
                
                return results
                
        except Exception as e:
            print(f"[VocabService] list_by_filters error: {e}")
            return []
    
    def get_distinct_sources(self, lang: str) -> List[str]:
        """Lấy danh sách các source_material đã có trong database.
        
        Args:
            lang: Language ("en" or "jp")
            
        Returns:
            List of unique source materials
        """
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            
            with get_session() as session:
                statement = select(Model.source_material).where(
                    Model.user_id == user_id,
                    Model.source_material != None,
                    Model.source_material != ""
                ).distinct()
                
                results = session.exec(statement).all()
                return [r for r in results if r]
                
        except Exception as e:
            print(f"[VocabService] get_distinct_sources error: {e}")
            return []
    
    def get_distinct_levels(self, lang: str) -> List[str]:
        """Lấy danh sách các level đã có trong database.
        
        Args:
            lang: Language ("en" or "jp")
            
        Returns:
            List of unique levels
        """
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            
            with get_session() as session:
                statement = select(Model.level).where(
                    Model.user_id == user_id,
                    Model.level != None,
                    Model.level != ""
                ).distinct()
                
                results = session.exec(statement).all()
                return [r for r in results if r]
                
        except Exception as e:
            print(f"[VocabService] get_distinct_levels error: {e}")
            return []
    
    def bulk_import(
        self,
        items: List[Dict[str, Any]],
        lang: str,
        default_topic_id: Optional[int] = None,
        default_source: Optional[str] = None,
        default_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import nhiều từ vựng cùng lúc từ CSV/Excel.
        
        Args:
            items: List of vocabulary dicts with keys: word, meaning, reading, etc.
            lang: Language ("en" or "jp")
            default_topic_id: Default topic to assign if not specified per item
            default_source: Default source_material if not specified per item
            default_level: Default level if not specified per item
            
        Returns:
            Dict with success count, error count, and error details
        """
        try:
            Model = self._get_model(lang)
            user_id = self.get_current_user_id()
            
            imported = 0
            skipped = 0
            errors = []
            
            with get_session() as session:
                for idx, item_data in enumerate(items):
                    try:
                        # Extract word field
                        if lang == "jp":
                            word_field = item_data.get("word") or item_data.get("word_kanji")
                        else:
                            word_field = item_data.get("word")
                        
                        if not word_field:
                            errors.append(f"Row {idx+1}: Missing word")
                            continue
                        
                        # Check for duplicates
                        if lang == "jp":
                            existing = session.exec(
                                select(Model).where(
                                    Model.user_id == user_id,
                                    Model.word_kanji == word_field
                                )
                            ).first()
                        else:
                            existing = session.exec(
                                select(Model).where(
                                    Model.user_id == user_id,
                                    Model.word == word_field
                                )
                            ).first()
                        
                        if existing:
                            skipped += 1
                            continue
                        
                        # Create new item
                        if lang == "jp":
                            new_item = Model(
                                user_id=user_id,
                                word_kanji=word_field,
                                word_kana=item_data.get("reading", ""),
                                meaning_vi=item_data.get("meaning", ""),
                                example_jp=item_data.get("example", ""),
                                user_note=item_data.get("note", ""),
                                topic_id=item_data.get("topic_id") or default_topic_id,
                                source_material=item_data.get("source") or default_source,
                                level=item_data.get("level") or default_level,
                                mastery_status=MasteryStatus.NEW.value,
                                tags=item_data.get("tags", "")
                            )
                        else:
                            new_item = Model(
                                user_id=user_id,
                                word=word_field,
                                ipa=item_data.get("reading", ""),
                                meaning_vi=item_data.get("meaning", ""),
                                example_en=item_data.get("example", ""),
                                user_note=item_data.get("note", ""),
                                topic_id=item_data.get("topic_id") or default_topic_id,
                                source_material=item_data.get("source") or default_source,
                                level=item_data.get("level") or default_level,
                                mastery_status=MasteryStatus.NEW.value,
                                tags=item_data.get("tags", "")
                            )
                        
                        session.add(new_item)
                        imported += 1
                        
                    except Exception as item_err:
                        errors.append(f"Row {idx+1}: {str(item_err)}")
                
                session.commit()
            
            return {
                "success": True,
                "imported": imported,
                "skipped": skipped,
                "errors": errors,
                "total_processed": len(items)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global singleton instance
_vocab_service: Optional[VocabService] = None


def get_vocab_service() -> VocabService:
    """Get global VocabService instance."""
    global _vocab_service
    if _vocab_service is None:
        _vocab_service = VocabService()
    return _vocab_service
