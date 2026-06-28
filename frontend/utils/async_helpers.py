"""Helper functions for running async code in PySide6."""
import asyncio
from typing import Callable, Any
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QApplication


# Keep references to threads to prevent garbage collection
_threads = []


class AsyncWorker(QObject):
    """Worker QObject that runs async code in a separate thread."""
    finished = Signal(object)
    
    def __init__(self, coro_func):
        super().__init__()
        self.coro_func = coro_func
    
    def run(self):
        """Run the async coroutine."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = None
        error = None
        try:
            # print(f"[DEBUG async_helpers] Starting coroutine")
            if asyncio.iscoroutine(self.coro_func):
                result = loop.run_until_complete(self.coro_func)
            else:
                result = loop.run_until_complete(self.coro_func())
            # print(f"[DEBUG async_helpers] Coroutine completed, result: {result}")
        except Exception as e:
            error = str(e)
            import traceback
            print(f"[DEBUG async_helpers] Error: {error}")
            print(traceback.format_exc())
        finally:
            loop.close()
        
        # Emit result signal (will be queued to main thread)
        if error:
            print(f"[DEBUG async_helpers] Emitting error signal: {error}")
            self.finished.emit({"error": error})
        else:
            # print(f"[DEBUG async_helpers] Emitting result signal: {result}")
            self.finished.emit(result if result is not None else {})


class CallbackInvoker(QObject):
    """QObject to invoke callbacks in main thread."""
    callback_signal = Signal(object)
    
    def __init__(self, callback_func):
        super().__init__()
        self.callback_func = callback_func
        self.callback_signal.connect(self._execute)
    
    def _execute(self, result):
        """Execute callback in main thread."""
        try:
            self.callback_func(result)
        except Exception as e:
            print(f"[DEBUG async_helpers] Error in callback: {e}")
            import traceback
            traceback.print_exc()


def run_async(coro: Callable, callback: Callable[[Any], None] = None):
    """Run async coroutine in a separate thread and optionally call callback with result in main thread.
    
    Args:
        coro: Async coroutine function to run
        callback: Optional callback function to call with result in main thread
    """
    if callback is None:
        # No callback, just run in background thread
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if asyncio.iscoroutine(coro):
                    loop.run_until_complete(coro)
                else:
                    loop.run_until_complete(coro())
            finally:
                loop.close()
        
        import threading
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        return
    
    # Use QThread with signal/slot for proper main thread callback
    app = QApplication.instance()
    if not app:
        # No QApplication, fallback to threading
        import threading
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = None
            error = None
            try:
                if asyncio.iscoroutine(coro):
                    result = loop.run_until_complete(coro)
                else:
                    result = loop.run_until_complete(coro())
            except Exception as e:
                error = str(e)
            finally:
                loop.close()
            
            if error:
                callback({"error": error})
            else:
                callback(result if result is not None else {})
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        return
    
    # Create worker and thread
    worker = AsyncWorker(coro)
    thread = QThread()
    worker.moveToThread(thread)
    
    # Keep references to prevent garbage collection
    _threads.append((thread, worker))
    
    # Create callback invoker and move to main thread
    invoker = CallbackInvoker(callback)
    invoker.moveToThread(app.thread())
    
    # Connect signals - use QueuedConnection to ensure callback runs in main thread
    from PySide6.QtCore import Qt, QTimer
    
    def on_finished(result):
        # Use signal to invoke callback in main thread
        invoker.callback_signal.emit(result)
        
        # Clean up thread after a delay
        def cleanup():
            thread.quit()
            if (thread, worker) in _threads:
                _threads.remove((thread, worker))
            # Delete after thread finishes
            thread.finished.connect(lambda: thread.deleteLater())
            thread.finished.connect(lambda: worker.deleteLater())
        QTimer.singleShot(500, cleanup)
    
    # Use QueuedConnection to ensure signal is queued to main thread
    worker.finished.connect(on_finished, Qt.ConnectionType.QueuedConnection)
    thread.started.connect(worker.run)
    
    thread.start()


def run_async_simple(coro: Callable):
    """Simple wrapper to run async coroutine without callback."""
    run_async(coro)

class AsyncHelper:
    """Helper class to manage async tasks from widgets."""
    def __init__(self, parent=None):
        self.parent = parent

    def run(self, coro, callback=None):
        """Run a coroutine asynchronously."""
        run_async(coro, callback)
