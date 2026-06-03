import math
import random
from datetime import datetime, timedelta, timezone


def forecast_demand(route_id):
    random.seed(42)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    forecast = []
    for i in range(1, 7):
        ds = now + timedelta(hours=i)
        morning = 8 * math.exp(-((ds.hour - 7) ** 2) / 5)
        evening = 9 * math.exp(-((ds.hour - 17.5) ** 2) / 5)
        yhat = max(1, min(16, 4 + morning + evening + random.uniform(-0.4, 0.4)))
        forecast.append({"ds": ds.isoformat(), "yhat": round(yhat, 2), "yhat_lower": round(max(0, yhat - 2.2), 2), "yhat_upper": round(min(16, yhat + 2.2), 2)})
    return forecast
