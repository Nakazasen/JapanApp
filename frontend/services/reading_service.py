"""Reading Service for book management and reading functionality.

Provides direct SQLite access for:
- Book management (list, get, upload)
- Chapter management  
- Reading positions
- Bookmarks

Uses local database instead of HTTP backend.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from sqlmodel import select

from frontend.core.database import get_session
from frontend.models import Book, BookChapter, ReadingState, Bookmark
from frontend.services.book_reader import EPUBReader, DOCXReader, MOBIReader, XLSXReader, PPTXReader
from frontend.services.base_service import BaseService


class ReadingService(BaseService):
    """Service for reading-related operations using local SQLite."""
    
    def get_books(self) -> List[Dict[str, Any]]:
        """Get all books for current user."""
        try:
            user_id = self.get_current_user_id()
            with get_session() as session:
                statement = select(Book).where(Book.user_id == user_id)
                books = session.exec(statement).all()
                return [
                    {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "file_format": book.file_format,
                        "total_chapters": book.total_chapters,
                        "created_at": book.created_at.isoformat() if book.created_at else None,
                    }
                    for book in books
                ]
        except Exception as e:
            print(f"[ReadingService] Error getting books: {e}")
            return []
    
    def get_book(self, book_id: int) -> Dict[str, Any]:
        """Get book details with chapters."""
        try:
            with get_session() as session:
                book = session.get(Book, book_id)
                if not book:
                    return {"error": "Book not found"}
                
                # Get chapters
                statement = select(BookChapter).where(
                    BookChapter.book_id == book_id
                ).order_by(BookChapter.chapter_index)
                chapters = session.exec(statement).all()
                
                return {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "file_format": book.file_format,
                    "total_chapters": book.total_chapters,
                    "chapters": [
                        {
                            "id": ch.id,
                            "chapter_index": ch.chapter_index,
                            "title": ch.title,
                            "word_count": ch.word_count,
                        }
                        for ch in chapters
                    ]
                }
        except Exception as e:
            print(f"[ReadingService] Error getting book: {e}")
            return {"error": str(e)}
    
    def get_chapter(self, book_id: int, chapter_id: int) -> Dict[str, Any]:
        """Get chapter content."""
        try:
            with get_session() as session:
                chapter = session.get(BookChapter, chapter_id)
                if not chapter or chapter.book_id != book_id:
                    return {"error": "Chapter not found"}
                
                return {
                    "id": chapter.id,
                    "chapter_index": chapter.chapter_index,
                    "title": chapter.title,
                    "content": chapter.content,
                    "html_content": chapter.html_content,
                    "word_count": chapter.word_count,
                }
        except Exception as e:
            print(f"[ReadingService] Error getting chapter: {e}")
            return {"error": str(e)}
    
    def upload_book(self, file_path: str) -> Dict[str, Any]:
        """Upload and parse a book file."""
        try:
            user_id = self.get_current_user_id()
            path = Path(file_path)
            
            if not path.exists():
                return {"error": "File not found"}
            
            # Determine reader based on extension
            ext = path.suffix.lower()
            if ext == ".epub":
                reader = EPUBReader(path)
            elif ext == ".docx":
                reader = DOCXReader(path)
            elif ext in [".mobi", ".prc", ".azw3"]:
                reader = MOBIReader(path)
            elif ext == ".xlsx":
                reader = XLSXReader(path)
            elif ext == ".pptx":
                reader = PPTXReader(path)
            else:
                return {"error": f"Unsupported file format: {ext}"}
            
            # Read book content
            book_data = reader.read()
            chapters = reader.get_chapters()
            
            with get_session() as session:
                # Create book
                book = Book(
                    user_id=user_id,
                    title=book_data.get("title", path.stem),
                    author=book_data.get("author", "Unknown"),
                    file_path=str(path),
                    file_format=ext.lstrip("."),
                    total_chapters=len(chapters),
                    created_at=datetime.utcnow(),
                )
                session.add(book)
                session.flush()  # Get book.id
                
                # Create chapters
                for idx, ch in enumerate(chapters):
                    chapter = BookChapter(
                        book_id=book.id,
                        chapter_index=idx,
                        title=ch.get("title", f"Chapter {idx + 1}"),
                        content=ch.get("content", ""),
                        html_content=ch.get("html_content", ""),
                        word_count=len(ch.get("content", "").split()),
                    )
                    session.add(chapter)
                
                session.commit()
                
                return {
                    "id": book.id,
                    "title": book.title,
                    "total_chapters": book.total_chapters,
                }
        except Exception as e:
            print(f"[ReadingService] Error uploading book: {e}")
            return {"error": str(e)}
    
    def get_reading_position(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get reading position for a book."""
        try:
            user_id = self.get_current_user_id()
            with get_session() as session:
                statement = select(ReadingState).where(
                    ReadingState.book_id == book_id,
                    ReadingState.user_id == user_id
                )
                state = session.exec(statement).first()
                
                if state:
                    return {
                        "chapter_index": state.chapter_index,
                        "position": state.position,
                        "last_read": state.last_read.isoformat() if state.last_read else None,
                    }
                return {"chapter_index": 0, "position": 0, "last_read": None}
        except Exception as e:
            print(f"[ReadingService] Error getting position: {e}")
            return None
    
    def save_reading_position(self, book_id: int, chapter_index: int, position: int) -> bool:
        """Save reading position."""
        try:
            user_id = self.get_current_user_id()
            with get_session() as session:
                statement = select(ReadingState).where(
                    ReadingState.book_id == book_id,
                    ReadingState.user_id == user_id
                )
                state = session.exec(statement).first()
                
                if state:
                    state.chapter_index = chapter_index
                    state.position = position
                    state.last_read = datetime.utcnow()
                else:
                    state = ReadingState(
                        user_id=user_id,
                        book_id=book_id,
                        chapter_index=chapter_index,
                        position=position,
                        last_read=datetime.utcnow(),
                    )
                    session.add(state)
                
                session.commit()
                return True
        except Exception as e:
            print(f"[ReadingService] Error saving position: {e}")
            return False
    
    def get_bookmarks(self, book_id: int) -> List[Dict[str, Any]]:
        """Get bookmarks for a book."""
        try:
            user_id = self.get_current_user_id()
            with get_session() as session:
                statement = select(Bookmark).where(
                    Bookmark.book_id == book_id,
                    Bookmark.user_id == user_id
                ).order_by(Bookmark.chapter_index, Bookmark.position)
                bookmarks = session.exec(statement).all()
                
                return [
                    {
                        "id": bm.id,
                        "chapter_index": bm.chapter_index,
                        "position": bm.position,
                        "note": bm.note,
                        "created_at": bm.created_at.isoformat() if bm.created_at else None,
                    }
                    for bm in bookmarks
                ]
        except Exception as e:
            print(f"[ReadingService] Error getting bookmarks: {e}")
            return []
    
    def add_bookmark(self, book_id: int, chapter_index: int, position: int, note: str = "") -> Dict[str, Any]:
        """Add a bookmark."""
        try:
            user_id = self.get_current_user_id()
            with get_session() as session:
                bookmark = Bookmark(
                    user_id=user_id,
                    book_id=book_id,
                    chapter_index=chapter_index,
                    position=position,
                    note=note,
                    created_at=datetime.utcnow(),
                )
                session.add(bookmark)
                session.commit()
                session.refresh(bookmark)
                
                return {"id": bookmark.id, "success": True}
        except Exception as e:
            print(f"[ReadingService] Error adding bookmark: {e}")
            return {"error": str(e)}


# Singleton
_reading_service: Optional[ReadingService] = None


def get_reading_service() -> ReadingService:
    """Get global ReadingService instance."""
    global _reading_service
    if _reading_service is None:
        _reading_service = ReadingService()
    return _reading_service
