import os
from typing import Dict, List
import pandas as pd


class TelemetryService:
    """
    Provides synthetic fleet state from CSV for MVP.
    Expected columns in data/vehicles.csv:
      id,battery_kwh,soc0,min_soc,depot_id,connector,max_kw,departure_hour,required_kwh
    """

    def __init__(self):
        root = os.path.dirname(os.path.dirname(__file__))
        self.vehicles_path = os.path.join(root, "data", "vehicles.csv")
        if not os.path.exists(self.vehicles_path):
            raise FileNotFoundError(f"Missing vehicles dataset at {self.vehicles_path}")
        self._vehicles_df = pd.read_csv(self.vehicles_path)

    def get_fleet_state(self) -> Dict[str, List[Dict]]:
        vehicles: List[Dict] = []
        for _, row in self._vehicles_df.iterrows():
            vehicles.append(
                {
                    "id": row["id"],
                    "battery_kwh": float(row["battery_kwh"]),
                    "soc0": float(row["soc0"]),
                    "min_soc": float(row["min_soc"]),
                    "depot_id": str(row["depot_id"]),
                    "connector": str(row["connector"]),
                    "max_kw": float(row["max_kw"]),
                    "departure_hour": int(row["departure_hour"]),
                    "required_kwh": float(row["required_kwh"]),
                }
            )
        return {"vehicles": vehicles}
