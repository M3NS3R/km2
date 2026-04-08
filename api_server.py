import asyncio
import uuid
from aiohttp import web
import json
from common.models import ForecastTask, TaskStatus
from common.logger_service import logger_service, LogLevel
from analysis_server import analysis_server

class APIHandler:
    """Single Responsibility: Обработка HTTP запросов"""
    
    def __init__(self):
        self.analysis_server = analysis_server
    
    async def post_forecast(self, request: web.Request) -> web.Response:
        """POST /forecast - создание задачи прогнозирования"""
        try:
            data = await request.json()
            
            # Генерация forecast_id
            forecast_id = str(uuid.uuid4())
            
            # Создание задачи
            task = ForecastTask(
                task_id=forecast_id,
                historical_hours=data.get('historical_hours', 5000),
                horizon=data.get('horizon', 48),
                season_factor=data.get('season_factor', 1.5)
            )
            
            # Отправка в очередь
            self.analysis_server.submit_task(task)
            
            logger_service.log("API Server", LogLevel.INFO, forecast_id, 
                              f"Task accepted: historical_hours={task.historical_hours}")
            
            return web.json_response({
                "forecast_id": forecast_id,
                "status": "accepted"
            }, status=202)
            
        except Exception as e:
            logger_service.log("API Server", LogLevel.ERROR, "UNKNOWN", f"Error: {str(e)}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def get_status(self, request: web.Request) -> web.Response:
        """GET /status/{forecast_id} - получение статуса"""
        forecast_id = request.match_info.get('forecast_id')
        
        # Обновляем результаты перед проверкой
        self.analysis_server.update_results()
        
        task = self.analysis_server.get_task_status(forecast_id)
        
        if not task:
            logger_service.log("API Server", LogLevel.WARNING, forecast_id, "Task not found")
            return web.json_response({"error": "Task not found"}, status=404)
        
        response = {
            "forecast_id": forecast_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
        
        if task.error_message:
            response["error"] = task.error_message
        
        logger_service.log("API Server", LogLevel.INFO, forecast_id, f"Status checked: {task.status.value}")
        
        return web.json_response(response)
    
    async def get_forecast(self, request: web.Request) -> web.Response:
        """GET /forecast/{forecast_id} - получение прогноза"""
        forecast_id = request.match_info.get('forecast_id')
        
        # Обновляем результаты
        self.analysis_server.update_results()
        
        task = self.analysis_server.get_task_status(forecast_id)
        
        if not task:
            return web.json_response({"error": "Task not found"}, status=404)
        
        if task.status != TaskStatus.COMPLETED:
            return web.json_response({
                "error": f"Forecast not ready. Current status: {task.status.value}"
            }, status=409)
        
        result = self.analysis_server.get_result(forecast_id)
        
        logger_service.log("API Server", LogLevel.INFO, forecast_id, "Forecast retrieved")
        
        return web.json_response({
            "forecast_id": forecast_id,
            "forecast": result['forecast'][:48],  # Первые 48 часов
            "peak_load": result['peak'],
            "horizon": result['horizon']
        })

class APIServer:
    """Liskov Substitution: Можно заменить на другой HTTP сервер"""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.handler = APIHandler()
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        self.app.router.add_post('/forecast', self.handler.post_forecast)
        self.app.router.add_get('/status/{forecast_id}', self.handler.get_status)
        self.app.router.add_get('/forecast/{forecast_id}', self.handler.get_forecast)
    
    async def start(self):
        """Запуск API сервера"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger_service.log("API Server", LogLevel.INFO, "SYSTEM", 
                          f"API Server started on http://{self.host}:{self.port}")
        
        # Держим сервер запущенным
        await asyncio.Event().wait()
    
    async def stop(self):
        """Остановка сервера"""
        await self.app.shutdown()
        logger_service.log("API Server", LogLevel.INFO, "SYSTEM", "API Server stopped")

async def main():
    # Запуск сервера анализа
    analysis_server.start()
    
    # Запуск API сервера
    api_server = APIServer()
    
    try:
        await api_server.start()
    except KeyboardInterrupt:
        await api_server.stop()
        analysis_server.stop()

if __name__ == '__main__':
    asyncio.run(main())