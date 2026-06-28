"""Reading models for book reading feature."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, ForeignKey, Relationship
from sqlalchemy import func, Text


class Book(SQLModel, table=True):
    """Book model for uploaded books."""
    __tablename__ = "books"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=500, index=True)
    author: Optional[str] = Field(default=None, max_length=200)
    file_path: str = Field(max_length=1000)  # Path to uploaded file
    file_format: str = Field(max_length=20)  # epub, docx, xlsx, pptx
    file_size: Optional[int] = Field(default=None)  # Size in bytes
    total_chapters: int = Field(default=0)
    book_metadata: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON string
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # Relationships
    chapters: list["BookChapter"] = Relationship(back_populates="book")
    reading_state: Optional["ReadingState"] = Relationship(back_populates="book")
    bookmarks: list["Bookmark"] = Relationship(back_populates="book")


class BookChapter(SQLModel, table=True):
    """Chapter model for book chapters."""
    __tablename__ = "book_chapters"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    chapter_index: int = Field(index=True)  # 0-based index
    title: str = Field(max_length=500)
    content: str = Field(sa_column=Column(Text))  # Full chapter content
    html_content: Optional[str] = Field(default=None, sa_column=Column(Text))  # HTML version
    word_count: Optional[int] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # Relationships
    book: Book = Relationship(back_populates="chapters")


class ReadingState(SQLModel, table=True):
    """Reading state model to track reading progress."""
    __tablename__ = "reading_states"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    book_id: int = Field(foreign_key="books.id", unique=True, index=True)
    chapter_index: int = Field(default=0)
    position: int = Field(default=0)  # Character position in chapter
    last_read: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # Relationships
    book: Book = Relationship(back_populates="reading_state")


class Bookmark(SQLModel, table=True):
    """Bookmark model for saving reading positions."""
    __tablename__ = "bookmarks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    chapter_index: int = Field(index=True)
    position: int = Field(default=0)  # Character position in chapter
    note: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # Relationships
    book: Book = Relationship(back_populates="bookmarks")

