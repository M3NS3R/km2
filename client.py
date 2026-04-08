import asyncio
import aiohttp
import json
from typing import Dict, Any

class ForecastClient:
    """Клиент для тестирования системы"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
    
    async def create_forecast(self, historical_hours: int, horizon: int, season_factor: float) -> Dict[str, Any]:
        """Создание задачи прогнозирования"""
        async with aiohttp.ClientSession() as session:
            data = {
                "historical_hours": historical_hours,
                "horizon": horizon,
                "season_factor": season_factor
            }
            async with session.post(f"{self.base_url}/forecast", json=data) as resp:
                return await resp.json()
    
    async def get_status(self, forecast_id: str) -> Dict[str, Any]:
        """Получение статуса"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/status/{forecast_id}") as resp:
                return await resp.json()
    
    async def get_forecast(self, forecast_id: str) -> Dict[str, Any]:
        """Получение прогноза"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/forecast/{forecast_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": await resp.text(), "status": resp.status}
    
    async def wait_for_completion(self, forecast_id: str, poll_interval: float = 2.0):
        """Ожидание завершения задачи"""
        while True:
            status_data = await self.get_status(forecast_id)
            status = status_data.get('status')
            
            if status in ['completed', 'failed']:
                return status_data
            elif status == 'queued':
                print("  Task is queued...")
            elif status == 'training':
                print("  Model training in progress...")
            elif status == 'forecasting':
                print("  Forecasting in progress...")
            
            await asyncio.sleep(poll_interval)

async def test_single_forecast():
    """Тест одного прогноза"""
    print("\n=== Test 1: Single Forecast ===")
    client = ForecastClient()
    
    # Создание задачи
    result = await client.create_forecast(
        historical_hours=2000,  # Уменьшено для теста
        horizon=48,
        season_factor=1.5
    )
    
    print(f"Task created: {result}")
    forecast_id = result['forecast_id']
    
    # Ожидание завершения
    final_status = await client.wait_for_completion(forecast_id)
    
    if final_status['status'] == 'completed':
        # Получение прогноза
        forecast = await client.get_forecast(forecast_id)
        print(f"\nForecast result: peak load = {forecast.get('peak_load', 'N/A')}")
        print(f"First 5 hours forecast: {forecast.get('forecast', [])[:5]}")
    else:
        print(f"Task failed: {final_status}")

async def test_multiple_concurrent():
    """Тест множества одновременных запросов"""
    print("\n=== Test 2: Multiple Concurrent Forecasts ===")
    client = ForecastClient()
    
    # Создание нескольких задач
    tasks = []
    for i in range(5):
        result = await client.create_forecast(
            historical_hours=1500,
            horizon=48,
            season_factor=1.2 + i * 0.1
        )
        tasks.append(result['forecast_id'])
        print(f"Created task {i+1}: {result['forecast_id'][:8]}...")
    
    # Ожидание всех задач
    for task_id in tasks:
        print(f"\nWaiting for {task_id[:8]}...")
        final_status = await client.wait_for_completion(task_id, poll_interval=1.0)
        if final_status['status'] == 'completed':
            forecast = await client.get_forecast(task_id)
            print(f"  Completed! Peak load: {forecast.get('peak_load', 'N/A'):.2f}")
        else:
            print(f"  Failed!")

async def test_status_checking():
    """Тест проверки статуса"""
    print("\n=== Test 3: Status Checking ===")
    client = ForecastClient()
    
    # Создание тяжелой задачи
    result = await client.create_forecast(
        historical_hours=5000,
        horizon=48,
        season_factor=2.0
    )
    
    forecast_id = result['forecast_id']
    print(f"Created heavy task: {forecast_id[:8]}...")
    
    # Проверка статуса несколько раз
    for i in range(5):
        await asyncio.sleep(1)
        status = await client.get_status(forecast_id)
        print(f"Check {i+1}: Status = {status.get('status')}")

async def main():
    """Основная функция тестирования"""
    print("Starting Energy Forecast System Tests")
    print("=" * 50)
    
    try:
        # Тест 1: Одиночный прогноз
        await test_single_forecast()
        
        # Тест 2: Множественные запросы
        await test_multiple_concurrent()
        
        # Тест 3: Проверка статуса
        await test_status_checking()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except aiohttp.ClientConnectionError:
        print("\nERROR: Cannot connect to API server.")
        print("Make sure api_server.py is running on http://localhost:8080")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == '__main__':
    asyncio.run(main())