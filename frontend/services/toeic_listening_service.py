"""TOEIC Listening Service.

Provides methods for loading and interacting with TOEIC Listening questions.
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from sqlmodel import select
from frontend.services.base_service import BaseService
from frontend.core.database import get_session
from frontend.models.toeic import ToeicQuestion, ToeicTest, ToeicUserProgress, ToeicStudySession, SessionType
from datetime import datetime


class ToeicListeningService(BaseService):
    """Service for TOEIC Listening practice."""
    
    def __init__(self):
        super().__init__()
        self._current_session_id: Optional[int] = None
    
    def list_parts(self) -> List[Dict[str, Any]]:
        """Get available listening parts with question counts."""
        parts_info = [
            {"part": 1, "name": "Part 1: Photos", "description": "Look at a photo and choose the best description.", "icon": "📷"},
            {"part": 2, "name": "Part 2: Question-Response", "description": "Listen to a question and choose the best response.", "icon": "💬"},
            {"part": 3, "name": "Part 3: Conversations", "description": "Listen to conversations between two people.", "icon": "👥"},
            {"part": 4, "name": "Part 4: Talks", "description": "Listen to talks by a single speaker.", "icon": "🎤"},
        ]
        
        try:
            with get_session() as session:
                for part in parts_info:
                    count = len(session.exec(
                        select(ToeicQuestion).where(ToeicQuestion.part == part["part"])
                    ).all())
                    part["count"] = count
        except Exception:
            for part in parts_info:
                part["count"] = 0
        
        return parts_info
    
    def list_questions(self, part: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get questions for a specific part."""
        try:
            with get_session() as session:
                questions = session.exec(
                    select(ToeicQuestion)
                    .where(ToeicQuestion.part == part)
                    .order_by(ToeicQuestion.question_number)
                    .limit(limit)
                ).all()
                
                return [
                    {
                        "id": q.id,
                        "part": q.part,
                        "question_type": q.question_type,
                        "difficulty": q.difficulty,
                        "topic": q.topic,
                        "question_text": q.question_text,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation,
                        "audio_path": q.audio_path,
                        "image_path": q.image_path,
                        "question_number": q.question_number,
                        "question_set_id": q.question_set_id, # Added field
                        "transcript": q.transcript # Added field
                    }
                    for q in questions
                ]
        except Exception as e:
            print(f"Error loading questions: {e}")
            return []

    def list_question_sets(self, part: int, limit: int = 20) -> List[Dict[str, Any]]:
        """List questions grouped by sets (for Part 3 & 4)."""
        try:
            with get_session() as session:
                # 1. Fetch questions for the part
                questions = session.exec(
                    select(ToeicQuestion)
                    .where(ToeicQuestion.part == part)
                    .order_by(ToeicQuestion.question_set_id, ToeicQuestion.question_number)
                ).all()
                
                # 2. Group by set_id
                sets_map = {}
                for q in questions:
                    # Use set_id or fake one if missing (shouldn't happen for part 3/4)
                    set_id = q.question_set_id or f"single_{q.id}"
                    
                    if set_id not in sets_map:
                        sets_map[set_id] = {
                            "set_id": set_id,
                            "part": q.part,
                            "audio_path": q.audio_path, # Shared audio (Part 3-4)
                            "transcript": q.transcript, # Shared transcript (Part 3-4)
                            "passage": q.passage,       # Shared passage (Part 6-7)
                            "topic": q.topic,
                            "questions": []
                        }
                    
                    sets_map[set_id]["questions"].append({
                        "id": q.id,
                        "question_number": q.question_number,
                        "question_text": q.question_text,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    })
                
                return list(sets_map.values())[:limit]
        except Exception as e:
            print(f"Error listing question sets: {e}")
            return []

    def get_test_details(self, test_id: int) -> Dict[str, Any]:
        """Get full details of a test with questions grouped by part."""
        with get_session() as session:
            # 1. Get Test Info
            test = session.get(ToeicTest, test_id)
            if not test:
                return {}
            
            # 2. Get Questions
            statement = select(ToeicQuestion).where(ToeicQuestion.test_id == test_id).order_by(ToeicQuestion.part, ToeicQuestion.question_number)
            questions = session.exec(statement).all()
            
            # 3. Group by Part
            parts_data = {}
            for part_num in range(1, 8):
                part_qs = [q for q in questions if q.part == part_num]
                if not part_qs: continue
                
                # Check if this part uses Sets
                if part_num in [3, 4, 6, 7]:
                    # Group by Set
                    sets_map = {}
                    for q in part_qs:
                        set_id = q.question_set_id or f"single_{q.id}"
                        if set_id not in sets_map:
                            sets_map[set_id] = {
                                "set_id": set_id,
                                "part": part_num,
                                "audio_path": q.audio_path,
                                "transcript": q.transcript,
                                "passage": q.passage,
                                "topic": q.topic,
                                "questions": []
                            }
                        sets_map[set_id]["questions"].append({
                            "id": q.id,
                            "question_text": q.question_text,
                            "options": q.options,
                            "question_number": q.question_number
                        })
                    parts_data[part_num] = list(sets_map.values())
                else:
                    # Single items
                    parts_data[part_num] = [
                        {
                            "id": q.id,
                            "part": part_num,
                            "question_text": q.question_text,
                            "options": q.options,
                            "audio_path": q.audio_path,
                            "image_path": q.image_path,
                            "question_number": q.question_number
                        }
                        for q in part_qs
                    ]
            
            return {
                "id": test.id,
                "name": test.name,
                "time_limit": test.time_limit,
                "parts": parts_data
            }

    def submit_test(self, test_id: int, user_answers: Dict[int, str]) -> Dict[str, Any]:
        """Submit test answers and calculate score."""
        with get_session() as session:
            # Get correct answers
            statement = select(ToeicQuestion).where(ToeicQuestion.test_id == test_id)
            questions = session.exec(statement).all()
            
            correct_count = 0
            details = {}
            
            for q in questions:
                user_ans = user_answers.get(q.id)
                is_correct = (user_ans == q.correct_answer)
                if is_correct:
                    correct_count += 1
                
                details[q.id] = {
                    "user_answer": user_ans,
                    "correct_answer": q.correct_answer,
                    "is_correct": is_correct
                }
            
            # Save Session Result
            # (Simplified scoring: 5 points per question for MVP)
            score = correct_count * 5 
            
            result = ToeicStudySession(
                user_id=1,
                session_type=SessionType.TEST.value,
                test_id=test_id,
                correct_count=correct_count,
                total_count=len(questions),
                estimated_score=score,
                is_completed=True,
                ended_at=datetime.utcnow()
            )
            session.add(result)
            session.commit()
            
            return {
                "score": score,
                "correct_count": correct_count,
                "total_count": len(questions),
                "details": details
            }
    
    def get_question(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Get a single question by ID."""
        try:
            with get_session() as session:
                q = session.get(ToeicQuestion, question_id)
                if not q:
                    return None
                return {
                    "id": q.id,
                    "part": q.part,
                    "question_type": q.question_type,
                    "difficulty": q.difficulty,
                    "topic": q.topic,
                    "question_text": q.question_text,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "audio_path": q.audio_path,
                    "image_path": q.image_path,
                }
        except Exception:
            return None

    def analyze_weaknesses(self) -> Dict[str, Any]:
        """Analyze user progress to identify weak areas."""
        try:
            with get_session() as session:
                user_id = self.get_current_user_id()
                progress = session.exec(
                    select(ToeicUserProgress).where(ToeicUserProgress.user_id == user_id)
                ).all()

                if not progress:
                    return {}

                # 1. Aggregate stats by Part and Topic
                part_stats = {}
                topic_stats = {}
                
                # Need to join with Question to get Part/Topic
                # For now, lazy load questions
                q_ids = [p.question_id for p in progress]
                questions = session.exec(select(ToeicQuestion).where(ToeicQuestion.id.in_(q_ids))).all()
                q_map = {q.id: q for q in questions}

                for p in progress:
                    q = q_map.get(p.question_id)
                    if not q: continue
                    
                    # By Part
                    if q.part not in part_stats:
                        part_stats[q.part] = {"correct": 0, "total": 0}
                    part_stats[q.part]["total"] += 1
                    if p.is_correct:
                        part_stats[q.part]["correct"] += 1
                        
                    # By Topic
                    topic = q.topic or "General"
                    if topic not in topic_stats:
                        topic_stats[topic] = {"correct": 0, "total": 0}
                    topic_stats[topic]["total"] += 1
                    if p.is_correct:
                        topic_stats[topic]["correct"] += 1

                # 2. Calculate Percentages & Identify Weaknesses (< 60%)
                weak_parts = []
                for part, data in part_stats.items():
                    acc = (data["correct"] / data["total"]) * 100
                    data["accuracy"] = acc
                    if acc < 60:
                        weak_parts.append({"part": part, "accuracy": acc})
                
                weak_topics = []
                for topic, data in topic_stats.items():
                    if data["total"] < 3: continue # Ignore if too few samples
                    acc = (data["correct"] / data["total"]) * 100
                    data["accuracy"] = acc
                    if acc < 60:
                        weak_topics.append({"topic": topic, "accuracy": acc})

                return {
                    "part_stats": part_stats,
                    "topic_stats": topic_stats,
                    "weak_parts": sorted(weak_parts, key=lambda x: x["accuracy"]),
                    "weak_topics": sorted(weak_topics, key=lambda x: x["accuracy"])
                }
        except Exception as e:
            print(f"Error analyzing weaknesses: {e}")
            return {}

    async def generate_ai_advice(self) -> str:
        """Generate personalized advice using Gemini AI (Cached)."""
        import json
        import hashlib
        from pathlib import Path
        
        try:
            stats = self.analyze_weaknesses()
            if not stats:
                return "Not enough data to generate advice. Please practice more!"
            
            # 1. Create Cache Key (Hash of stats)
            # Use specific parts that affect advice (weak parts list + total count)
            # This ensures if user does more tests, cache is invalidated
            # Simplified hash: based on number of answers + correct count per part
            # Or just use the raw weak_parts list which contains accuracy
            cache_base = {
                "user_id": self.get_current_user_id(),
                "part_stats": stats.get("part_stats")
            }
            stats_str = json.dumps(cache_base, sort_keys=True)
            stats_hash = hashlib.md5(stats_str.encode()).hexdigest()
            
            # 2. Check Cache
            cache_dir = Path("data/cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / "ai_advice_cache.json"
            
            cache_data = {}
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                except:
                    pass
            
            user_cache_key = str(self.get_current_user_id())
            user_cache = cache_data.get(user_cache_key, {})
            
            # If hash matches, return cached advice
            if user_cache.get("hash") == stats_hash and user_cache.get("advice"):
                print("Returning cached AI advice.")
                return user_cache["advice"]

            # 3. Generate New Advice (Cache Miss)
            # Format Prompt
            weak_parts_str = ", ".join([f"Part {x['part']} ({x['accuracy']:.1f}%)" for x in stats.get("weak_parts", [])])
            weak_topics_str = ", ".join([f"{x['topic']} ({x['accuracy']:.1f}%)" for x in stats.get("weak_topics", [])])
            
            prompt = (
                f"You are a TOEIC Coach. Analyze this student's performance:\n"
                f"- Weak Parts: {weak_parts_str or 'None (Good job!)'}\n"
                f"- Weak Topics: {weak_topics_str or 'None'}\n\n"
                f"Provide concise, actionable advice (max 3 bullet points) to improve their score. "
                f"Focus on specific strategies for the weak parts. Tone: Encouraging."
            )
            
            from frontend.core.gemini_client import get_gemini_client
            client = get_gemini_client()
            advice = client.generate_text(prompt)
            
            # 4. Save to Cache
            if advice and "unavailable" not in advice.lower():
                cache_data[user_cache_key] = {
                    "hash": stats_hash,
                    "advice": advice,
                    "timestamp": datetime.utcnow().isoformat()
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return advice
            
        except Exception as e:
            print(f"Error generating AI advice: {e}")
            return "AI Coach is currently unavailable."
    
    def check_answer(self, question_id: int, user_answer: str) -> Dict[str, Any]:
        """Check if the user's answer is correct."""
        try:
            with get_session() as session:
                q = session.get(ToeicQuestion, question_id)
                if not q:
                    return {"success": False, "error": "Question not found"}
                
                is_correct = user_answer.upper() == q.correct_answer.upper()
                
                return {
                    "success": True,
                    "is_correct": is_correct,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "user_answer": user_answer,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_progress(self, question_id: int, user_answer: str, is_correct: bool, time_spent: int = 0) -> bool:
        """Save the user's answer to a question."""
        try:
            with get_session() as session:
                progress = ToeicUserProgress(
                    user_id=self.get_current_user_id(),
                    question_id=question_id,
                    session_id=self._current_session_id,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    time_spent=time_spent,
                )
                session.add(progress)
                session.commit()
                return True
        except Exception as e:
            print(f"Error saving progress: {e}")
            return False
    
    def start_session(self, part: int) -> int:
        """Start a new study session for a specific part."""
        try:
            with get_session() as session:
                study_session = ToeicStudySession(
                    user_id=self.get_current_user_id(),
                    session_type=SessionType.LISTENING.value,
                    part=part,
                )
                session.add(study_session)
                session.commit()
                session.refresh(study_session)
                self._current_session_id = study_session.id
                return study_session.id
        except Exception as e:
            print(f"Error starting session: {e}")
            return -1
    
    def end_session(self, correct_count: int, total_count: int) -> bool:
        """End the current study session."""
        if not self._current_session_id:
            return False
        
        try:
            with get_session() as session:
                study_session = session.get(ToeicStudySession, self._current_session_id)
                if study_session:
                    study_session.ended_at = datetime.utcnow()
                    study_session.correct_count = correct_count
                    study_session.total_count = total_count
                    study_session.is_completed = True
                    session.add(study_session)
                    session.commit()
                self._current_session_id = None
                return True
        except Exception as e:
            print(f"Error ending session: {e}")
            return False
    
    def get_stats(self, part: Optional[int] = None) -> Dict[str, Any]:
        """Get listening practice statistics."""
        try:
            with get_session() as session:
                user_id = self.get_current_user_id()
                
                # Total questions
                query = select(ToeicQuestion)
                if part:
                    query = query.where(ToeicQuestion.part == part)
                else:
                    query = query.where(ToeicQuestion.part.in_([1, 2, 3, 4]))
                total_questions = len(session.exec(query).all())
                
                # Progress
                progress_query = select(ToeicUserProgress).where(ToeicUserProgress.user_id == user_id)
                all_progress = session.exec(progress_query).all()
                
                answered_ids = set()
                correct_count = 0
                for p in all_progress:
                    answered_ids.add(p.question_id)
                    if p.is_correct:
                        correct_count += 1
                
                return {
                    "total_questions": total_questions,
                    "answered": len(answered_ids),
                    "correct": correct_count,
                    "accuracy": round(correct_count / len(answered_ids) * 100, 1) if answered_ids else 0,
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total_questions": 0, "answered": 0, "correct": 0, "accuracy": 0}
            
    def get_ai_analysis(self, question_id: int) -> str:
        """Get AI analysis for a specific question."""
        try:
            with get_session() as session:
                q = session.get(ToeicQuestion, question_id)
                if not q:
                    return "Question not found."
                
                # TODO: Integrate with actual Gemini API
                # For now, return a template using the explanation
                analysis = (
                    f"🤖 **AI Analysis**\n\n"
                    f"**Topic:** {q.topic or 'General'}\n"
                    f"**Why the answer is {q.correct_answer}:**\n"
                    f"{q.explanation or 'No explanation provided.'}\n\n"
                    f"**Tips:** Listen for keywords related to '{q.topic or 'context'}'. "
                    f"Eliminate options that sound similar but have different meanings (distractors)."
                )
                return analysis
        except Exception as e:
            return f"Error analyzing question: {e}"

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get aggregated stats for dashboard."""
        try:
            with get_session() as session:
                user_id = self.get_current_user_id()
                
                # Fetch all progress
                progress = session.exec(
                    select(ToeicUserProgress).where(ToeicUserProgress.user_id == user_id)
                ).all()
                
                # Fetch all questions to map parts
                all_questions = session.exec(select(ToeicQuestion)).all()
                q_map = {q.id: q for q in all_questions}
                
                stats = {
                    "total_answered": len(progress),
                    "total_correct": 0,
                    "listening_correct": 0,
                    "reading_correct": 0,
                    "listening_total_answered": 0,
                    "reading_total_answered": 0,
                    "part_stats": {i: {"correct": 0, "total": 0} for i in range(1, 8)}
                }
                
                for p in progress:
                    q = q_map.get(p.question_id)
                    if not q: continue
                    
                    if p.is_correct:
                        stats["total_correct"] += 1
                        stats["part_stats"][q.part]["correct"] += 1
                        if q.part <= 4:
                            stats["listening_correct"] += 1
                        else:
                            stats["reading_correct"] += 1
                            
                    stats["part_stats"][q.part]["total"] += 1
                    if q.part <= 4:
                        stats["listening_total_answered"] += 1
                    else:
                        stats["reading_total_answered"] += 1

                # Calculate Scores (Simple projection)
                # Max score per section is 495.
                def estimate_score(correct, total, max_score=495):
                    if total == 0: return 5 # Minimum score
                    accuracy = correct / total
                    return int(max(5, accuracy * max_score))

                stats["listening_score"] = estimate_score(
                    stats["listening_correct"], 
                    stats["listening_total_answered"]
                )
                
                stats["reading_score"] = estimate_score(
                    stats["reading_correct"], 
                    stats["reading_total_answered"]
                )
                
                stats["total_score"] = stats["listening_score"] + stats["reading_score"]
                
                # Overall Accuracy
                if stats["total_answered"] > 0:
                     stats["accuracy"] = round(stats["total_correct"] / stats["total_answered"] * 100, 1)
                else:
                     stats["accuracy"] = 0.0
                
                return stats
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {}


# Singleton instance
_service = None

def get_toeic_listening_service() -> ToeicListeningService:
    """Get the TOEIC Listening service singleton."""
    global _service
    if _service is None:
        _service = ToeicListeningService()
    return _service
