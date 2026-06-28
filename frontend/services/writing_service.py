"""Writing Service - AI-powered writing assistance (no HTTP backend).

This service provides:
- Writing topic generation using Gemini directly
- Writing review and feedback using Gemini directly
- Draft management via local SQLite (TODO: implement if needed)
"""
from typing import List, Dict, Optional, Any

from datetime import datetime
from sqlmodel import select
from frontend.services.base_service import BaseService
from frontend.core.gemini_client import get_gemini_handler
from frontend.core.database import get_session
from frontend.models.writing import WritingDraft


class WritingService(BaseService):
    """Service for AI-powered writing assistance.
    
    Uses Gemini directly instead of HTTP backend.
    """
    
    def __init__(self):
        """Initialize writing service."""
    # ========== Draft Management ==========
    
    def save_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a writing draft."""
        try:
            with get_session() as session:
                if draft_data.get("id"):
                    # Update existing
                    draft = session.get(WritingDraft, draft_data["id"])
                    if not draft:
                        return {"success": False, "error": "Draft not found"}
                    
                    draft.title = draft_data.get("title", draft.title)
                    draft.content = draft_data.get("content", draft.content)
                    draft.language = draft_data.get("language", draft.language)
                    draft.updated_at = datetime.utcnow()
                else:
                    # Create new
                    draft = WritingDraft(
                        title=draft_data.get("title", "Untitled"),
                        content=draft_data.get("content", ""),
                        language=draft_data.get("language", "en"),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(draft)
                
                session.commit()
                session.refresh(draft)
                return draft.model_dump()
        except Exception as e:
            print(f"[ERROR WritingService] Failed to save draft: {e}")
            return {"success": False, "error": str(e)}

    def get_drafts(self) -> List[Dict[str, Any]]:
        """Get all drafts ordered by update time."""
        try:
            with get_session() as session:
                statement = select(WritingDraft).order_by(WritingDraft.updated_at.desc())
                results = session.exec(statement).all()
                return [d.model_dump() for d in results]
        except Exception as e:
            print(f"[ERROR WritingService] Failed to get drafts: {e}")
            return []

    def delete_draft(self, draft_id: int) -> Dict[str, Any]:
        """Delete a draft."""
        try:
            with get_session() as session:
                draft = session.get(WritingDraft, draft_id)
                if draft:
                    session.delete(draft)
                    session.commit()
                    return {"ok": True}
                return {"ok": False, "error": "Draft not found"}
        except Exception as e:
            print(f"[ERROR WritingService] Failed to delete draft: {e}")
            return {"ok": False, "error": str(e)}

    # ========== AI Features ==========
    
    def generate_topic(self, lang: str = "en", level: str = "intermediate") -> Dict[str, Any]:
        """Generate a writing topic using Gemini directly.
        
        Args:
            lang: Language ("en" or "jp")
            level: Difficulty level ("beginner", "intermediate", "advanced")
            
        Returns:
            Dict with success and topic
        """
        level_name = {
            "beginner": "beginner (A1-A2)", 
            "intermediate": "intermediate (B1-B2)", 
            "advanced": "advanced (C1-C2)"
        }.get(level, level)
        
        if lang == "jp":
            prompt = f"""日本語学習者（{level_name}）向けの、面白くて書きやすいトピックを1つ生成してください。
150〜300字程度の作文に適したトピックにしてください。
トピック文のみを日本語で返してください。"""
        else:
            prompt = f"""Generate a short, engaging writing topic for a {level_name} student learning English.
The topic should be:
- Interesting and thought-provoking
- Appropriate for a 150-300 word essay
- Clear and specific

Return ONLY the topic sentence in English, nothing else."""

        try:
            handler = get_gemini_handler()
            response = handler.generate_text(prompt, temperature=0.8)
            return {"success": True, "topic": response.strip()}
        except Exception as e:
            print(f"[ERROR WritingService] Failed to generate topic: {e}")
            return {"success": False, "error": str(e)}

    def review_writing(self, text: str, lang: str = "en") -> Dict[str, Any]:
        """Review writing with Gemini and return structured feedback.
        
        Args:
            text: The writing to review
            lang: Language ("en" or "jp")
            
        Returns:
            Dict with score, corrections, and feedback
        """
        if lang == "jp":
            prompt = f"""あなたは日本語教師です。以下の作文を添削してください。

作文:
{text}

以下の形式で返答してください:
1. スコア (0-10): [数字のみ]
2. 訂正版: [訂正された文章]
3. フィードバック: 
- 良い点
- 改善点
- 文法の注意点"""
        else:
            prompt = f"""You are an English writing teacher. Review the following essay and provide feedback.

Essay:
{text}

Provide your response in this format:
1. Score (0-10): [number only]
2. Corrected version: [the corrected text]
3. Feedback:
- Strengths
- Areas for improvement  
- Grammar tips"""

        try:
            handler = get_gemini_handler()
            response = handler.generate_text(prompt, temperature=0.3)
            
            # Parse response (simplified - in production would be more robust)
            lines = response.split('\n')
            score = 7.0  # Default score
            corrected_text = text
            feedback_lines = []
            
            in_feedback = False
            in_corrected = False
            
            for line in lines:
                line_lower = line.lower().strip()
                
                # Extract score
                if 'score' in line_lower or 'スコア' in line:
                    try:
                        # Find number in line
                        import re
                        numbers = re.findall(r'[\d.]+', line)
                        if numbers:
                            score = float(numbers[0])
                            score = min(10, max(0, score))
                    except:
                        pass
                
                # Collect feedback
                if 'feedback' in line_lower or 'フィードバック' in line:
                    in_feedback = True
                    in_corrected = False
                elif in_feedback:
                    if line.strip().startswith('-') or line.strip().startswith('•'):
                        feedback_lines.append(line.strip())
                
                # Collect corrected text
                if 'corrected' in line_lower or '訂正版' in line:
                    in_corrected = True
                    in_feedback = False
                    corrected_text = ""
                elif in_corrected and line.strip():
                    corrected_text += line + "\n"
            
            return {
                "success": True,
                "score": round(score, 1),
                "corrected_text": corrected_text.strip() or text,
                "detailed_feedback": feedback_lines,
                "general_comment": feedback_lines[0] if feedback_lines else "Bài viết của bạn đã được phân tích.",
                "raw_response": response
            }
            
        except Exception as e:
            print(f"[ERROR WritingService] Failed to review writing: {e}")
            return {"success": False, "error": str(e)}
    
    def improve_sentence(self, sentence: str, lang: str = "en") -> Dict[str, Any]:
        """Suggest improvements for a single sentence.
        
        Args:
            sentence: The sentence to improve
            lang: Language
            
        Returns:
            Dict with improved versions
        """
        if lang == "jp":
            prompt = f"""この文を改善してください: "{sentence}"

3つの改善版を提供してください：
1. 文法的に正しい版
2. より自然な版
3. よりフォーマルな版"""
        else:
            prompt = f"""Improve this sentence: "{sentence}"

Provide 3 improved versions:
1. Grammatically correct version
2. More natural version
3. More formal version

Just provide the 3 sentences, numbered."""

        try:
            handler = get_gemini_handler()
            response = handler.generate_text(prompt, temperature=0.5)
            
            return {
                "success": True,
                "original": sentence,
                "suggestions": response.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global singleton
_writing_service: Optional[WritingService] = None


def get_writing_service() -> WritingService:
    """Get global WritingService instance."""
    global _writing_service
    if _writing_service is None:
        _writing_service = WritingService()
    return _writing_service
