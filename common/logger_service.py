import threading
import logging
from datetime import datetime
from common.queue import LogQueue
from common.models import LogMessage, LogLevel

class LoggerService:
    """Лог-сервер на threading для неблокирующего логирования"""
    
    def __init__(self, log_file: str = "system.log"):
        self.log_queue = LogQueue()
        self.log_file = log_file
        self.running = True
        self.thread = threading.Thread(target=self._process_logs, daemon=True)
        self.thread.start()
        
        # Настройка файлового логгера
        self.file_logger = logging.getLogger('SystemLogger')
        self.file_logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.file_logger.addHandler(handler)
    
    def _process_logs(self):
        """Обработчик очереди логов"""
        while self.running:
            try:
                log_msg = self.log_queue.get()
                log_entry = f"[{log_msg.service}] [{log_msg.level.value}] [{log_msg.task_id}] {log_msg.message}"
                self.file_logger.info(log_entry)
                print(log_entry)  # Также выводим в консоль
            except Exception as e:
                print(f"Logger error: {e}")
    
    def log(self, service: str, level: LogLevel, task_id: str, message: str):
        """Неблокирующее логирование"""
        log_msg = LogMessage(
            timestamp=datetime.now(),
            service=service,
            level=level,
            task_id=task_id,
            message=message
        )
        self.log_queue.put(log_msg)
    
    def stop(self):
        self.running = False

# Глобальный экземпляр
logger_service = LoggerService()