import multiprocessing as mp
import time
import math
from typing import Dict, Any, Optional
from common.models import ForecastTask, TaskStatus
from common.logger_service import logger_service, LogLevel

class ForecastEngine:
    """Single Responsibility: Вычисление прогноза"""
    
    @staticmethod
    def calculate(task: ForecastTask) -> Dict[str, Any]:
        """CPU-bound задача прогнозирования"""
        historical_hours = task.historical_hours
        horizon = task.horizon
        season_factor = task.season_factor
        
        forecast = []
        for h in range(horizon):
            val = 0.0
            for i in range(historical_hours):
                val += (math.sin(i * season_factor) * 
                       math.cos(h * i / 1000) * 
                       math.sqrt(abs(i - h)))
            forecast.append(val % 1000)
        
        return {
            "forecast": forecast,
            "peak": max(forecast),
            "horizon": horizon
        }


# ВЫНОСИМ ФУНКЦИЮ ВНЕ КЛАССА
def process_tasks(task_queue: mp.Queue, result_queue: mp.Queue):
    """Функция для обработки задач в отдельном процессе"""
    engine = ForecastEngine()
    
    while True:
        task = None
        try:
            task = task_queue.get(timeout=1)
            if task is None:  # Сигнал остановки
                break
            
            logger_service.log("AnalysisServer", LogLevel.INFO, task.task_id, "Started processing")
            
            # Этап тренировки (имитация)
            task.status = TaskStatus.TRAINING
            time.sleep(1)
            logger_service.log("AnalysisServer", LogLevel.INFO, task.task_id, "Training phase completed")
            
            # Этап прогнозирования
            task.status = TaskStatus.FORECASTING
            result = engine.calculate(task)
            time.sleep(0.5)
            
            task.forecast_result = result
            task.status = TaskStatus.COMPLETED
            logger_service.log("AnalysisServer", LogLevel.INFO, task.task_id, f"Forecast completed. Peak: {result['peak']:.2f}")
            
            result_queue.put(task)
            
        except Exception as e:
            if task is not None:
                logger_service.log("AnalysisServer", LogLevel.ERROR, task.task_id, f"Failed: {str(e)}")
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                result_queue.put(task)
            else:
                logger_service.log("AnalysisServer", LogLevel.ERROR, "UNKNOWN", f"Error in process loop: {str(e)}")


class AnalysisServer:
    """Dependency Inversion: Зависит от абстракций очередей"""
    
    def __init__(self, num_workers: int = None):
        if num_workers is None:
            num_workers = mp.cpu_count()
        
        self.num_workers = num_workers
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.processes = []
        self.tasks_store = {}  # In-memory store (для демо)
    
    def start(self):
        """Запуск пула процессов"""
        for i in range(self.num_workers):
            p = mp.Process(target=process_tasks, args=(self.task_queue, self.result_queue))
            p.start()
            self.processes.append(p)
        logger_service.log("AnalysisServer", LogLevel.INFO, "SYSTEM", 
                          f"Started with {self.num_workers} workers")
    
    def submit_task(self, task: ForecastTask):
        """Отправить задачу на обработку"""
        self.tasks_store[task.task_id] = task
        self.task_queue.put(task)
        logger_service.log("AnalysisServer", LogLevel.INFO, task.task_id, "Task queued for processing")
        return task.task_id
    
    def get_task_status(self, task_id: str) -> Optional[ForecastTask]:
        """Получить статус задачи"""
        return self.tasks_store.get(task_id)
    
    def get_result(self, task_id: str) -> Optional[dict]:
        """Получить результат прогноза"""
        task = self.tasks_store.get(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.forecast_result
        return None
    
    def update_results(self):
        """Обновление результатов из очереди"""
        try:
            while not self.result_queue.empty():
                completed_task = self.result_queue.get_nowait()
                self.tasks_store[completed_task.task_id] = completed_task
                logger_service.log("AnalysisServer", LogLevel.INFO, completed_task.task_id, "Result stored")
        except:
            pass
    
    def stop(self):
        """Остановка всех процессов"""
        for _ in self.processes:
            self.task_queue.put(None)
        for p in self.processes:
            p.join(timeout=5)
        logger_service.log("AnalysisServer", LogLevel.INFO, "SYSTEM", "Server stopped")


# Глобальный экземпляр
analysis_server = AnalysisServer()