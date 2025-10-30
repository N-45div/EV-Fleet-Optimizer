from datetime import datetime, timedelta
from typing import List


class PriceService:
    """
    Synthetic time-of-use price curve generator (USD/kWh) for MVP.
    Pattern (local time):
      00:00–06:00: 0.12 (off-peak)
      06:00–12:00: 0.20
      12:00–18:00: 0.28 (peak)
      18:00–22:00: 0.32 (super-peak)
      22:00–24:00: 0.18
    """

    def __init__(self):
        pass

    def _price_for_hour_of_day(self, hour: int) -> float:
        if 0 <= hour < 6:
            return 0.12
        if 6 <= hour < 12:
            return 0.20
        if 12 <= hour < 18:
            return 0.28
        if 18 <= hour < 22:
            return 0.32
        return 0.18

    def get_prices(self, horizon_hours: int) -> List[float]:
        now = datetime.utcnow()
        prices: List[float] = []
        for t in range(horizon_hours):
            ts = now + timedelta(hours=t)
            prices.append(self._price_for_hour_of_day(ts.hour))
        return prices
