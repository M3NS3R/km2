from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class TaskStatus(Enum):
    QUEUED = "queued"
    TRAINING = "training"
    FORECASTING = "forecasting"
    COMPLETED = "completed"
    FAILED = "failed"

class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class ForecastTask:
    task_id: str
    historical_hours: int
    horizon: int
    season_factor: float
    status: TaskStatus = TaskStatus.QUEUED
    forecast_result: Optional[Dict] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class LogMessage:
    timestamp: datetime
    service: str
    level: LogLevel
    task_id: str
    message: str