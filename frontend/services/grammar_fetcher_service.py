"""Grammar Fetcher Service - Search grammar topics."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select, col, or_
from frontend.core.database import get_session
from frontend.models.grammar import GrammarTopic, GrammarMasteryStatus, GrammarCategory
from frontend.models.study import StudyHistory
from frontend.services.srs_service import SRSService

class GrammarFetcherService:
    """Service to fetch and manage grammar topics."""
    
    def search_grammar(self, lang: str, query: str, session: Session) -> List[GrammarTopic]:
        """Search grammar topics by title or description."""
        if not query:
            return []
            
        statement = select(GrammarTopic).where(
            GrammarTopic.lang == lang,
            or_(
                col(GrammarTopic.title).contains(query),
                col(GrammarTopic.description).contains(query)
            )
        )
        return session.exec(statement).all()

    # =============== Category Management ===============
    
    def create_category(self, name: str, lang: str, description: str = None) -> Dict[str, Any]:
        """Create a new grammar category/topic group."""
        try:
            with get_session() as session:
                category = GrammarCategory(
                    name=name,
                    lang=lang,
                    description=description
                )
                session.add(category)
                session.commit()
                session.refresh(category)
                return {"success": True, "id": category.id, "name": category.name}
        except Exception as e:
            return {"error": str(e)}

    def list_categories(self, lang: str, session: Session) -> List[GrammarCategory]:
        """List all grammar categories for a language."""
        statement = select(GrammarCategory).where(GrammarCategory.lang == lang)
        return session.exec(statement).all()
        if not query:
            return []
            
        statement = select(GrammarTopic).where(
            GrammarTopic.lang == lang,
            or_(
                col(GrammarTopic.title).contains(query),
                col(GrammarTopic.description).contains(query)
            )
        )
        return session.exec(statement).all()

    def bookmark_grammar(self, grammar_id: int, session: Session) -> bool:
        """Toggle bookmark status for a grammar topic."""
        item = session.get(GrammarTopic, grammar_id)
        if item:
            item.is_bookmarked = not item.is_bookmarked
            session.add(item)
            session.commit()
            session.refresh(item)
            return item.is_bookmarked
        return False
        
    def list_all(self, lang: str, session: Session) -> List[Dict[str, Any]]:
        """List all grammar topics for a language."""
        statement = select(GrammarTopic).where(GrammarTopic.lang == lang)
        items = session.exec(statement).all()
        # Convert to dicts to avoid DetachedInstanceError
        return [self._topic_to_dict(item) for item in items]
        
    def get_due(
        self, 
        lang: str, 
        session: Session, 
        limit: int = 20,
        category_id: Optional[int] = None,
        source_material: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get grammar topics due for review with optional filters."""
        conditions = [GrammarTopic.lang == lang]
        
        if category_id is not None:
            conditions.append(GrammarTopic.category_id == category_id)
        if source_material:
            conditions.append(GrammarTopic.source_material == source_material)
        if level:
            conditions.append(GrammarTopic.level == level)
            
        statement = select(GrammarTopic).where(*conditions)
        items = session.exec(statement).all()
        
        due_items = []
        now = datetime.utcnow()
        
        for item in items:
            if item.mastery_status == GrammarMasteryStatus.NEW.value or item.mastery_status is None:
                due_items.append(item)
            elif item.last_reviewed_at:
                days_since = (now - item.last_reviewed_at).days
                if item.next_review_at and item.next_review_at <= now:
                    due_items.append(item)
                elif not item.next_review_at:
                    due_items.append(item)
                    
            if len(due_items) >= limit:
                break
                
        # Convert to dicts to avoid DetachedInstanceError
        return [self._topic_to_dict(item) for item in due_items]
    
    def _topic_to_dict(self, item: GrammarTopic) -> Dict[str, Any]:
        """Convert GrammarTopic ORM object to dictionary."""
        return {
            "id": item.id,
            "title": item.title,
            "pattern": item.pattern,
            "description": item.description,
            "level": item.level,
            "usage_notes": item.usage_notes,
            "mastery_status": item.mastery_status,
            "is_bookmarked": item.is_bookmarked,
            "is_ai_enriched": item.is_ai_enriched,
            "last_reviewed_at": item.last_reviewed_at,
            "next_review_at": item.next_review_at,
            "srs_level": item.srs_level,
            "srs_streak": item.srs_streak
        }
        
    def submit_review(self, grammar_id: int, quality: int, session: Session) -> bool:
        """Submit review for grammar point.
        
        Quality: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
        """
        item = session.get(GrammarTopic, grammar_id)
        if not item:
            return False
            
        item.last_reviewed_at = datetime.utcnow()
        
        # Centralized SRS Logic
        new_streak, new_ef, new_interval = SRSService.calculate_next_state(
            current_streak=item.srs_streak,
            current_ease_factor=item.srs_ease_factor,
            current_interval=item.srs_interval,
            quality=quality
        )
        
        item.srs_streak = new_streak
        item.srs_ease_factor = new_ef
        item.srs_interval = new_interval
        item.next_review_at = SRSService.get_next_review_date(new_interval)
        item.review_count += 1
        
        # Update Mastery Status based on streak/interval
        if quality == 1:
            item.mastery_status = GrammarMasteryStatus.HARD.value
        elif new_interval > 21:
            item.mastery_status = GrammarMasteryStatus.MASTERED.value
        else:
            item.mastery_status = GrammarMasteryStatus.LEARNING.value
            
        session.add(item)
        
        # Record study history for dashboard/gamification
        try:
            from frontend.services.base_service import BaseService
            user_id = BaseService.get_current_user_id()
            if user_id:
                history = StudyHistory(
                    user_id=user_id,
                    vocab_id=grammar_id,
                    lang=item.lang,
                    study_date=datetime.utcnow(),
                    words_reviewed=1,
                    status=item.mastery_status
                )
                session.add(history)
        except Exception as e:
            print(f"[GrammarFetcherService] Failed to record study history: {e}")
            
        session.commit()
        return True
    
    def add_grammar(self, grammar_data: Dict[str, Any], lang: str, session: Session) -> Dict[str, Any]:
        """Add new grammar topic.
        
        Args:
            grammar_data: Dict with title, pattern, description, usage_notes, common_mistakes, level
            lang: Language (jp or en)
            session: Database session
            
        Returns:
            Result with success or error
        """
        try:
            topic = GrammarTopic(
                lang=lang,
                title=grammar_data.get("title"),
                pattern=grammar_data.get("pattern"),
                description=grammar_data.get("description"),
                usage_notes=grammar_data.get("usage_notes"),
                common_mistakes=grammar_data.get("common_mistakes"),
                level=grammar_data.get("level"),
                mastery_status=GrammarMasteryStatus.NEW.value,
                created_at=datetime.utcnow(),
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
            return {"success": True, "id": topic.id}
        except Exception as e:
            return {"error": str(e)}
    
    def delete_grammar(self, grammar_id: int, session: Session) -> Dict[str, Any]:
        """Delete a grammar topic.
        
        Args:
            grammar_id: ID of grammar to delete
            session: Database session
            
        Returns:
            Result with success or error
        """
        try:
            topic = session.get(GrammarTopic, grammar_id)
            if topic:
                session.delete(topic)
                session.commit()
                return {"success": True}
            return {"error": "Không tìm thấy ngữ pháp"}
        except Exception as e:
            return {"error": str(e)}
    
    def update_grammar(self, grammar_id: int, grammar_data: Dict[str, Any], session: Session) -> Dict[str, Any]:
        """Update a grammar topic.
        
        Args:
            grammar_id: ID of grammar to update
            grammar_data: Dict with fields to update
            session: Database session
            
        Returns:
            Result with success or error
        """
        try:
            topic = session.get(GrammarTopic, grammar_id)
            if topic:
                # Update provided fields
                if grammar_data.get("title"):
                    topic.title = grammar_data["title"]
                if grammar_data.get("pattern") is not None:
                    topic.pattern = grammar_data["pattern"]
                if grammar_data.get("description") is not None:
                    topic.description = grammar_data["description"]
                if grammar_data.get("usage_notes") is not None:
                    topic.usage_notes = grammar_data["usage_notes"]
                if grammar_data.get("common_mistakes") is not None:
                    topic.common_mistakes = grammar_data["common_mistakes"]
                if grammar_data.get("level"):
                    topic.level = grammar_data["level"]
                if grammar_data.get("source_material") is not None:
                    topic.source_material = grammar_data["source_material"]
                if "is_ai_enriched" in grammar_data:
                    topic.is_ai_enriched = grammar_data["is_ai_enriched"]
                
                topic.last_updated = datetime.utcnow()
                session.add(topic)
                session.commit()
                return {"success": True}
            return {"error": "Không tìm thấy ngữ pháp"}
        except Exception as e:
            return {"error": str(e)}
    
    # =============== Advanced Filtering ===============
    
    def list_by_filters(
        self,
        lang: str,
        session: Session,
        category_id: Optional[int] = None,
        source_material: Optional[str] = None,
        level: Optional[str] = None,
        mastery_statuses: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Lọc ngữ pháp theo nhiều tiêu chí.
        
        Args:
            lang: Language ("en" or "jp")
            session: Database session
            category_id: Filter by category ID
            source_material: Filter by curriculum source
            level: Filter by level
            mastery_statuses: List of statuses to include
            search_query: Search in title/pattern
            limit: Maximum results
            
        Returns:
            List of grammar items matching filters
        """
        try:
            # Build query conditions
            conditions = [GrammarTopic.lang == lang]
            
            if category_id is not None:
                conditions.append(GrammarTopic.category_id == category_id)
            
            if source_material:
                conditions.append(GrammarTopic.source_material == source_material)
            
            if level:
                conditions.append(GrammarTopic.level == level)
            
            if mastery_statuses:
                conditions.append(GrammarTopic.mastery_status.in_(mastery_statuses))
            
            if search_query:
                search_pattern = f"%{search_query}%"
                conditions.append(
                    or_(
                        col(GrammarTopic.title).like(search_pattern),
                        col(GrammarTopic.pattern).like(search_pattern),
                        col(GrammarTopic.description).like(search_pattern)
                    )
                )
            
            statement = select(GrammarTopic).where(*conditions).limit(limit)
            items = session.exec(statement).all()
            
            return [self._topic_to_dict_extended(item) for item in items]
            
        except Exception as e:
            print(f"[GrammarFetcherService] list_by_filters error: {e}")
            return []
    
    def _topic_to_dict_extended(self, item: GrammarTopic) -> Dict[str, Any]:
        """Convert GrammarTopic to dict with extended fields."""
        return {
            "id": item.id,
            "title": item.title,
            "pattern": item.pattern,
            "description": item.description,
            "level": item.level,
            "source_material": item.source_material,
            "usage_notes": item.usage_notes,
            "common_mistakes": item.common_mistakes,
            "mastery_status": item.mastery_status,
            "category_id": item.category_id,
            "tags": item.tags,
            "is_bookmarked": item.is_bookmarked,
            "is_ai_enriched": item.is_ai_enriched,
            "last_reviewed_at": str(item.last_reviewed_at) if item.last_reviewed_at else None,
            "created_at": str(item.created_at) if item.created_at else None,
        }
    
    def get_distinct_sources(self, lang: str, session: Session) -> List[str]:
        """Lấy danh sách các source_material đã có trong database.
        
        Args:
            lang: Language ("en" or "jp")
            session: Database session
            
        Returns:
            List of unique source materials
        """
        try:
            statement = select(GrammarTopic.source_material).where(
                GrammarTopic.lang == lang,
                GrammarTopic.source_material != None,
                GrammarTopic.source_material != ""
            ).distinct()
            
            results = session.exec(statement).all()
            return [r for r in results if r]
            
        except Exception as e:
            print(f"[GrammarFetcherService] get_distinct_sources error: {e}")
            return []
    
    def get_distinct_levels(self, lang: str, session: Session) -> List[str]:
        """Lấy danh sách các level đã có trong database.
        
        Args:
            lang: Language ("en" or "jp")
            session: Database session
            
        Returns:
            List of unique levels
        """
        try:
            statement = select(GrammarTopic.level).where(
                GrammarTopic.lang == lang,
                GrammarTopic.level != None,
                GrammarTopic.level != ""
            ).distinct()
            
            results = session.exec(statement).all()
            return [r for r in results if r]
            
        except Exception as e:
            print(f"[GrammarFetcherService] get_distinct_levels error: {e}")
            return []
    
    def bulk_import(
        self,
        items: List[Dict[str, Any]],
        lang: str,
        session: Session,
        default_category_id: Optional[int] = None,
        default_source: Optional[str] = None,
        default_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import nhiều ngữ pháp cùng lúc từ CSV/Excel.
        
        Args:
            items: List of grammar dicts with keys: title, pattern, description, etc.
            lang: Language ("en" or "jp")
            session: Database session
            default_category_id: Default category to assign
            default_source: Default source_material
            default_level: Default level
            
        Returns:
            Dict with success count, error count, and error details
        """
        try:
            imported = 0
            skipped = 0
            errors = []
            
            for idx, item_data in enumerate(items):
                try:
                    title = item_data.get("title", "").strip()
                    
                    if not title:
                        errors.append(f"Row {idx+1}: Missing title")
                        continue
                    
                    # Check for duplicates
                    existing = session.exec(
                        select(GrammarTopic).where(
                            GrammarTopic.lang == lang,
                            GrammarTopic.title == title
                        )
                    ).first()
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    # Create new item
                    new_item = GrammarTopic(
                        lang=lang,
                        title=title,
                        pattern=item_data.get("pattern", ""),
                        description=item_data.get("description", item_data.get("meaning", "")),
                        usage_notes=item_data.get("usage_notes", item_data.get("usage", "")),
                        common_mistakes=item_data.get("common_mistakes", ""),
                        category_id=item_data.get("category_id") or default_category_id,
                        source_material=item_data.get("source") or default_source,
                        level=item_data.get("level") or default_level,
                        mastery_status=GrammarMasteryStatus.NEW.value,
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

