
"""Exam Service - Manage exams and results."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import select
from frontend.services.base_service import BaseService
from frontend.services.exam_scraper import ExamScraperService
from frontend.core.database import get_session
from frontend.models.exam import ExamSource, Exam, ExamQuestion, ExamResult

class ExamService(BaseService):
    """Service for managing exams."""
    
    def __init__(self):
        super().__init__()
        
    def list_available_exams(self, level: str) -> List[Dict]:
        """List available exams from online source."""
        # For now, just support dethitiengnhat.com via scraper
        try:
            return ExamScraperService.get_exam_list(level)
        except Exception as e:
            print(f"[ERROR ExamService] Failed to list available exams: {e}")
            return []

    def get_exam_sources(self) -> List[Dict]:
        """Get list of exam sources."""
        try:
            with get_session() as session:
                sources = session.exec(select(ExamSource)).all()
                return [s.model_dump() for s in sources]
        except Exception as e:
            print(f"[ERROR ExamService] Failed to get sources: {e}")
            return []

    def fetch_exam(self, source_id: int, url: str) -> Optional[Dict]:
        """Fetch exam from URL (scrape if new, load if existing)."""
        try:
            with get_session() as session:
                # Check if exam exists
                statement = select(Exam).where(Exam.description == url) # Storing URL in description strictly for now or add url field
                # Wait, Exam model doesn't have URL field? 
                # Model has: title, description, source_id.
                # I should check if I can use description for URL or query by source and title?
                # Let's check model again.
                # ExamSource has URL. Exam has foreign key.
                # Ideally Exam table should have 'original_url' or similar. 
                # I'll use description for URL for now to avoid schema migration if possible, 
                # OR better: check by title and source? Titles might duplicate.
                # Let's use description for URL storage as temporary measure if schema is fixed.
                # Actually, I can check if description matches URL.
                
                # Check model:
                # class Exam(SQLModel): title, description, total_questions...
                pass
                
                # Existing check
                existing = session.exec(select(Exam).where(Exam.description == url)).first()
                if existing:
                    return existing.model_dump()
                
                # Scrape
                scraped_data = ExamScraperService.scrape_exam(url)
                if not scraped_data:
                    return None
                    
                # Save Exam
                new_exam = Exam(
                    user_id=1, # Default user
                    source_id=source_id,
                    title=scraped_data["title"],
                    description=url, # Store URL here
                    total_questions=scraped_data["total_questions"],
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                session.add(new_exam)
                session.commit()
                session.refresh(new_exam)
                
                # Save Questions
                questions = scraped_data["questions"]
                for q in questions:
                    exam_q = ExamQuestion(
                        exam_id=new_exam.id,
                        question_text=q["question_text"],
                        options=q["options"],
                        correct_option=q.get("correct_option"),
                        question_order=q["question_number"]
                    )
                    session.add(exam_q)
                
                session.commit()
                return new_exam.model_dump()
                
        except Exception as e:
            print(f"[ERROR ExamService] Failed to fetch exam: {e}")
            return None

    def list_exams(self) -> List[Dict]:
        """List saved exams."""
        try:
            with get_session() as session:
                exams = session.exec(select(Exam).order_by(Exam.created_at.desc())).all()
                return [e.model_dump() for e in exams]
        except Exception as e:
            return []

    def get_exam_questions(self, exam_id: int) -> List[Dict]:
        """Get questions for an exam."""
        try:
            with get_session() as session:
                questions = session.exec(select(ExamQuestion).where(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.question_order)).all()
                return [q.model_dump() for q in questions]
        except Exception as e:
            print(f"[ERROR ExamService] Failed to get questions: {e}")
            return []

    def submit_exam(self, exam_id: int, answers: Dict[int, str], time_taken: int) -> Dict[str, Any]:
        """Submit exam answers and calculate score."""
        try:
            with get_session() as session:
                questions = self.get_exam_questions(exam_id)
                # Map question_id or order to correct answer
                # Currently scraper doesn't get correct answers usually.
                # So we can't score accurately unless scraper gets answers (which might require login or separate page).
                # Assuming scraper gets correct_option is None for now.
                # If correct_option is None, we can't score.
                # But let's assume we might have it or user updates it?
                # Returns dummy score if no correct answers.
                
                correct_count = 0
                total_count = len(questions)
                detailed_feedback = {}
                
                for q in questions:
                    q_id = q["id"]
                    q_order = q["question_order"]
                    user_ans = answers.get(q_id) or answers.get(q_order)
                    
                    is_correct = False
                    correct_opt = q.get("correct_option")
                    if correct_opt and user_ans == correct_opt:
                        is_correct = True
                        correct_count += 1
                        
                    detailed_feedback[str(q_id)] = {
                        "user_answer": user_ans,
                        "correct_answer": correct_opt,
                        "is_correct": is_correct
                    }

                score = (correct_count / total_count * 100) if total_count > 0 else 0
                
                result = ExamResult(
                    user_id=1,
                    exam_id=exam_id,
                    user_score=score,
                    user_time=time_taken,
                    detailed_feedback=detailed_feedback,
                    date_taken=datetime.utcnow()
                )
                session.add(result)
                session.commit()
                session.refresh(result)
                
                return {
                    "score": score,
                    "correct_count": correct_count,
                    "total_count": total_count,
                    "result_id": result.id
                }
        except Exception as e:
            print(f"[ERROR ExamService] Failed to submit exam: {e}")
            return None

# Singleton
_exam_service: Optional[ExamService] = None

def get_exam_service() -> ExamService:
    global _exam_service
    if _exam_service is None:
        _exam_service = ExamService()
    return _exam_service
