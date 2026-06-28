"""Background sync service for automatic news updates.

Features:
- Auto-refresh news every 30 minutes
- Cache new articles to SQLite
- Emit signal when new articles are available
- Pause sync when app is inactive
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Callable
from PySide6.QtCore import QObject, QTimer, Signal, QThread

from frontend.services.news.aggregator import TechHubAggregator
from frontend.services.news.cache_service import NewsCacheService
from frontend.services.news.base_client import Article


class BackgroundSyncWorker(QObject):
    """Worker for background fetching in separate thread."""
    
    finished = Signal(list, int)  # (articles, new_count)
    error = Signal(str)
    
    def __init__(self, mode: str = "mixed"):
        super().__init__()
        self.mode = mode
        self._aggregator = TechHubAggregator()
    
    def run(self):
        """Fetch articles in background."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            articles = loop.run_until_complete(
                self._aggregator.fetch_all(
                    mode=self.mode,
                    max_articles=30
                )
            )
            
            loop.close()
            
            # Cache articles and count new ones
            cache = NewsCacheService(user_id=1)
            new_count = cache.cache_articles(articles)
            
            self.finished.emit(articles, new_count)
            
        except Exception as e:
            import traceback
            print(f"[BackgroundSync] Error: {e}")
            traceback.print_exc()
            self.error.emit(str(e))


class BackgroundSyncService(QObject):
    """Service for automatic background news synchronization.
    
    Usage:
        sync_service = BackgroundSyncService()
        sync_service.new_articles_available.connect(on_new_articles)
        sync_service.start()
    """
    
    # Signal emitted when new articles are available
    new_articles_available = Signal(int)  # Number of new articles
    sync_started = Signal()
    sync_completed = Signal(int)  # Total articles fetched
    sync_error = Signal(str)
    
    # Default sync interval: 30 minutes
    DEFAULT_INTERVAL_MS = 30 * 60 * 1000  # 30 minutes
    MIN_INTERVAL_MS = 5 * 60 * 1000       # 5 minutes minimum
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        
        self._is_syncing = False
        self._is_enabled = True
        self._mode = "mixed"
        self._interval_ms = self.DEFAULT_INTERVAL_MS
        self._last_sync: Optional[datetime] = None
        self._total_syncs = 0
        
        self._worker: Optional[BackgroundSyncWorker] = None
        self._worker_thread: Optional[QThread] = None
        
        print("[BackgroundSync] Service initialized")
    
    @property
    def is_syncing(self) -> bool:
        return self._is_syncing
    
    @property
    def last_sync(self) -> Optional[datetime]:
        return self._last_sync
    
    @property
    def next_sync_in_minutes(self) -> int:
        """Minutes until next sync."""
        if not self._timer.isActive():
            return -1
        return self._timer.remainingTime() // 60000
    
    def set_interval(self, minutes: int):
        """Set sync interval in minutes."""
        ms = max(minutes * 60 * 1000, self.MIN_INTERVAL_MS)
        self._interval_ms = ms
        
        if self._timer.isActive():
            self._timer.setInterval(ms)
        
        print(f"[BackgroundSync] Interval set to {minutes} minutes")
    
    def set_mode(self, mode: str):
        """Set sync mode (global/japan/mixed)."""
        self._mode = mode
        print(f"[BackgroundSync] Mode set to {mode}")
    
    def start(self):
        """Start background sync service."""
        if self._timer.isActive():
            print("[BackgroundSync] Already running")
            return
        
        self._is_enabled = True
        self._timer.start(self._interval_ms)
        print(f"[BackgroundSync] Started with interval {self._interval_ms // 60000} minutes")
        
        # Optionally do initial sync after a short delay
        QTimer.singleShot(5000, self._check_initial_sync)
    
    def stop(self):
        """Stop background sync service."""
        self._is_enabled = False
        self._timer.stop()
        
        # Cancel any running worker
        if self._worker:
            self._cleanup_worker()
        
        print("[BackgroundSync] Stopped")
    
    def pause(self):
        """Temporarily pause syncing."""
        self._timer.stop()
        print("[BackgroundSync] Paused")
    
    def resume(self):
        """Resume syncing after pause."""
        if self._is_enabled and not self._timer.isActive():
            self._timer.start(self._interval_ms)
            print("[BackgroundSync] Resumed")
    
    def sync_now(self):
        """Trigger immediate sync."""
        if self._is_syncing:
            print("[BackgroundSync] Sync already in progress")
            return
        
        self._do_sync()
    
    def _check_initial_sync(self):
        """Check if initial sync is needed."""
        # Check if we have recent cached articles
        cache = NewsCacheService(user_id=1)
        cached = cache.get_cached_articles(limit=1)
        
        if not cached:
            print("[BackgroundSync] No cached articles, doing initial sync")
            self._do_sync()
        else:
            print("[BackgroundSync] Found cached articles, skipping initial sync")
    
    def _on_timer_tick(self):
        """Handle timer tick."""
        if self._is_syncing:
            print("[BackgroundSync] Skipping tick, sync in progress")
            return
        
        self._do_sync()
    
    def _do_sync(self):
        """Perform the actual sync."""
        if self._is_syncing:
            return
        
        self._is_syncing = True
        self.sync_started.emit()
        print(f"[BackgroundSync] Starting sync #{self._total_syncs + 1} (mode: {self._mode})")
        
        # Create worker and thread
        self._worker = BackgroundSyncWorker(mode=self._mode)
        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        
        # Connect signals
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.error.connect(self._on_sync_error)
        self._worker.finished.connect(self._cleanup_worker)
        self._worker.error.connect(self._cleanup_worker)
        
        # Start
        self._worker_thread.start()
    
    def _on_sync_finished(self, articles: List[Article], new_count: int):
        """Handle sync completion."""
        self._is_syncing = False
        self._last_sync = datetime.now()
        self._total_syncs += 1
        
        print(f"[BackgroundSync] Sync completed: {len(articles)} articles, {new_count} new")
        
        self.sync_completed.emit(len(articles))
        
        if new_count > 0:
            self.new_articles_available.emit(new_count)
    
    def _on_sync_error(self, error: str):
        """Handle sync error."""
        self._is_syncing = False
        print(f"[BackgroundSync] Sync error: {error}")
        self.sync_error.emit(error)
    
    def _cleanup_worker(self):
        """Clean up worker and thread."""
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait(1000)
            self._worker_thread = None
        self._worker = None


# Global singleton instance
_sync_service: Optional[BackgroundSyncService] = None


def get_background_sync_service() -> BackgroundSyncService:
    """Get singleton instance of BackgroundSyncService."""
    global _sync_service
    if _sync_service is None:
        _sync_service = BackgroundSyncService()
    return _sync_service
