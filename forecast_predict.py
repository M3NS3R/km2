import time
def load_forecast(historical_hours: int, horizon: int, season_factor: float) -> dict:
    import math
    forecast = []
    for h in range(horizon):
        val = 0
        for i in range(historical_hours):
            val += math.sin(i * season_factor) * math.cos(h * i / 1000) * math.sqrt(abs(i - h))
        forecast.append(val % 1000)
    return {"forecast": forecast[:10], "peak": max(forecast)}

a = time.time()
load_forecast(historical_hours = 118760, horizon = 128 , season_factor = 2 )
b = time.time()
print(b-a)