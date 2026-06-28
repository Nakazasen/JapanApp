"""Pomodoro Service to handle session tracking."""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from frontend.core.database import get_session
from frontend.models.study import PomodoroSession
from frontend.services.base_service import BaseService


class PomodoroService(BaseService):
    """Service to manage Pomodoro statistics."""
    
    def log_session(self, duration_mins: int, mode: str = "work") -> bool:
        """Log a completed Pomodoro session."""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return False
                
            with get_session() as session:
                new_session = PomodoroSession(
                    user_id=user_id,
                    duration_minutes=duration_mins,
                    mode=mode,
                    completed_at=datetime.utcnow()
                )
                session.add(new_session)
                session.commit()
                return True
        except Exception as e:
            print(f"[PomodoroService] Error logging session: {e}")
            return False
            
    def get_stats(self) -> Dict[str, Any]:
        """Get Pomodoro statistics for the current user."""
        try:
            user_id = self.get_current_user_id()
            if not user_id:
                return {"total_count": 0, "today_count": 0, "total_minutes": 0}
                
            now = datetime.utcnow()
            today_start = datetime(now.year, now.month, now.day)
            
            with get_session() as session:
                # Total sessions
                statement = select(func.count(PomodoroSession.id)).where(
                    PomodoroSession.user_id == user_id,
                    PomodoroSession.mode == "work"
                )
                total_count = session.exec(statement).one()
                
                # Today sessions
                statement_today = select(func.count(PomodoroSession.id)).where(
                    PomodoroSession.user_id == user_id,
                    PomodoroSession.mode == "work",
                    PomodoroSession.completed_at >= today_start
                )
                today_count = session.exec(statement_today).one()
                
                # Total focus time
                statement_time = select(func.sum(PomodoroSession.duration_minutes)).where(
                    PomodoroSession.user_id == user_id,
                    PomodoroSession.mode == "work"
                )
                total_minutes = session.exec(statement_time).one() or 0
                
                return {
                    "total_count": total_count,
                    "today_count": today_count,
                    "total_minutes": total_minutes
                }
        except Exception as e:
            print(f"[PomodoroService] Error fetching stats: {e}")
            return {"total_count": 0, "today_count": 0, "total_minutes": 0}

_instance = None

def get_pomodoro_service():
    global _instance
    if _instance is None:
        _instance = PomodoroService()
    return _instance
