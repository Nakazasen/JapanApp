"""Frontend Services Package.

This package provides modular services for the desktop app:
- AuthService: Authentication and user management (local SQLite)
- VocabService: Vocabulary CRUD and SRS (local SQLite)
- StatsService: Dashboard statistics and gamification (local SQLite)
- MediaService: TTS and audio playback
- WritingService: AI writing assistance (Gemini direct)
- AIConfigManager: Gemini AI configuration

Content Services (moved from backend):
- TranslatorService: Translation between languages
- TTSService: Text-to-speech synthesis
- NewsScraperService: News article scraping
- YouTubeService: YouTube video info and transcripts
- EPUBReader, DOCXReader, MOBIReader: Book readers
- GrammarFetcherService: Grammar content fetching
- ExamScraperService: Exam content scraping

Usage:
    from frontend.services import get_vocab_service, get_translator_service
    
    vocab = get_vocab_service()
    result = vocab.search("hello", "en")  # Now sync, not async
"""
from frontend.services.base_service import BaseService, ServiceError, APIError
from frontend.services.auth_service import AuthService, get_auth_service
from frontend.services.vocab_service import VocabService, get_vocab_service
from frontend.services.stats_service import StatsService, get_stats_service
from frontend.services.media_service import MediaService, get_media_service
from frontend.services.writing_service import WritingService, get_writing_service
from frontend.services.ai_service import AIConfigManager, get_config_manager, get_ai_service

# Content services (moved from backend)
from frontend.services.translator import TranslatorService, get_translator_service
from frontend.services.tts import TTSService, get_tts_service
from frontend.services.news_scraper import NewsScraperService
from frontend.services.youtube_service import YouTubeService
# Book readers
from frontend.services.book_reader import EPUBReader, DOCXReader, XLSXReader, PPTXReader, MOBIReader
# Grammar and exam scrapers will be loaded on demand due to potential import issues
# from frontend.services.grammar_fetcher import GrammarFetcherService
# from frontend.services.exam_scraper import ExamScraperService

__all__ = [
    # Base
    "BaseService",
    "ServiceError",
    "APIError",
    
    # Auth
    "AuthService",
    "get_auth_service",
    
    # Vocab
    "VocabService", 
    "get_vocab_service",
    
    # Stats
    "StatsService",
    "get_stats_service",
    
    # Media
    "MediaService",
    "get_media_service",
    
    # Writing
    "WritingService",
    "get_writing_service",
    
    # AI
    "AIConfigManager",
    "get_config_manager",
    "get_ai_service",
    
    # Content Services (from backend)
    "TranslatorService",
    "get_translator_service",
    "TTSService",
    "get_tts_service",
    "NewsScraperService",
    "YouTubeService",
    # Book readers
    "EPUBReader",
    "DOCXReader",
    "XLSXReader", 
    "PPTXReader",
    "MOBIReader",
]
