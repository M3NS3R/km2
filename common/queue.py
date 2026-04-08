from queue import Queue
from threading import Lock

class LogQueue:
    """Потокобезопасная очередь для логов (Singleton)"""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._queue = Queue()
        return cls._instance
    
    def put(self, message):
        self._queue.put(message)
    
    def get(self):
        return self._queue.get()