"""Authentication Service - Local session management (no HTTP backend).

This service manages:
- User authentication (login/logout) via local SQLite
- User registration with password hashing
- Local session state management
"""
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

from sqlmodel import Session, select
from frontend.core.database import get_session
from frontend.models.user import User


class AuthError(Exception):
    """Custom exception for auth errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AuthService:
    """Service for local authentication operations.
    
    Uses SQLite database directly instead of HTTP backend.
    """
    
    # Current logged-in user
    _current_user: Optional[User] = None
    _current_user_id: Optional[int] = None
    
    def __init__(self):
        """Initialize auth service."""
        pass
    
    @classmethod
    def get_current_user_id(cls) -> Optional[int]:
        """Get current logged-in user ID."""
        return cls._current_user_id
    
    @classmethod
    def get_current_user(cls) -> Optional[User]:
        """Get current logged-in user."""
        return cls._current_user
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login with username and password.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Dict with user info or error
        """
        try:
            with get_session() as session:
                # Find user by username
                statement = select(User).where(User.username == username)
                user = session.exec(statement).first()
                
                if not user:
                    return {"error": "Tên đăng nhập không tồn tại"}
                
                # Check password
                password_hash = self._hash_password(password)
                if user.password_hash != password_hash:
                    return {"error": "Mật khẩu không đúng"}
                
                # Update last login
                user.last_login = datetime.utcnow()
                session.add(user)
                session.commit()
                session.refresh(user)
                
                # Store current user
                AuthService._current_user = user
                AuthService._current_user_id = user.id
                
                # IMPORTANT: Sync with BaseService so other services can see the user
                from frontend.services.base_service import BaseService
                BaseService.set_current_user(user.id)
                
                print(f"[AuthService] Login successful: {username} (ID: {user.id})")
                
                return {
                    "success": True,
                    "user_id": user.id,
                    "username": user.username,
                    "token": str(user.id)  # Simple token is user ID
                }
                
        except Exception as e:
            print(f"[AuthService] Login error: {e}")
            return {"error": f"Lỗi đăng nhập: {str(e)}"}
    
    def register(
        self, 
        username: str, 
        password: str, 
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new user.
        
        Args:
            username: Desired username
            password: User's password
            email: Optional email address
            
        Returns:
            Registration result
        """
        try:
            with get_session() as session:
                # Check if username exists
                existing = session.exec(
                    select(User).where(User.username == username)
                ).first()
                
                if existing:
                    return {"error": "Tên đăng nhập đã tồn tại"}
                
                # Create new user
                user = User(
                    username=username,
                    password_hash=self._hash_password(password),
                    email=email,
                    created_at=datetime.utcnow()
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                
                print(f"[AuthService] User registered: {username} (ID: {user.id})")
                
                return {
                    "success": True,
                    "user_id": user.id,
                    "username": user.username,
                    "message": "Đăng ký thành công!"
                }
                
        except Exception as e:
            print(f"[AuthService] Register error: {e}")
            return {"error": f"Lỗi đăng ký: {str(e)}"}
    
    def logout(self) -> Dict[str, Any]:
        """Logout and clear session.
        
        Returns:
            Logout confirmation
        """
        AuthService._current_user = None
        AuthService._current_user_id = None
        
        from frontend.services.base_service import BaseService
        BaseService.clear_current_user()
        
        print("[AuthService] User logged out")
        return {"message": "Đã đăng xuất", "success": True}
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated.
        
        Returns:
            True if logged in
        """
        return AuthService._current_user_id is not None
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information.
        
        Returns:
            User information dict
        """
        if not self._current_user:
            return {"error": "Chưa đăng nhập"}
        
        return {
            "id": self._current_user.id,
            "username": self._current_user.username,
            "email": self._current_user.email,
            "created_at": str(self._current_user.created_at),
            "last_login": str(self._current_user.last_login) if self._current_user.last_login else None
        }


# Global singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get global AuthService instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
