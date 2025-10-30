import os
from typing import Dict, List, Optional
import pandas as pd


class KGService:
    """
    MeTTa-style Grid Knowledge Graph adapter (MVP in Python).

    Sources:
      - data/chargers.csv: id,depot_id,connector,max_kw
      - kg/site_limits.csv: depot_id,site_peak_kw
    """

    def __init__(self, metta: Optional[object] = None):
        root = os.path.dirname(os.path.dirname(__file__))
        self.chargers_path = os.path.join(root, "data", "chargers.csv")
        self.site_limits_path = os.path.join(root, "kg", "site_limits.csv")

        if not os.path.exists(self.chargers_path):
            raise FileNotFoundError(f"Missing chargers dataset at {self.chargers_path}")
        self._chargers_df = pd.read_csv(self.chargers_path)

        if os.path.exists(self.site_limits_path):
            self._site_limits_df = pd.read_csv(self.site_limits_path)
        else:
            # sensible defaults
            self._site_limits_df = pd.DataFrame(
                {"depot_id": ["D1", "D2"], "site_peak_kw": [60.0, 60.0]}
            )

        # runtime overrides and windows
        self._site_peak_override: Dict[str, float] = {}
        # blackout windows per depot: list of (start_hour_inclusive, end_hour_exclusive)
        self._blackouts: Dict[str, List[List[int]]] = {}

        # MeTTa adapter (optional)
        self.metta = metta
        # enable if adapter present and environment flag USE_METTA=true
        self._use_metta = bool(self.metta) and str(os.getenv("USE_METTA", "false")).lower() in ("1", "true", "yes") and getattr(self.metta, "enabled", False)
        if self._use_metta:
            try:
                # Provide DF facts to MeTTa
                self.metta.load_facts(self._site_limits_df, self._chargers_df)
            except Exception:
                self._use_metta = False

    def get_depot_chargers(self, depot_id: str) -> List[Dict]:
        if self._use_metta and self.metta:
            from_metta = self.metta.query_chargers(depot_id)
            if from_metta:
                # decorate with depot_id
                for ch in from_metta:
                    ch["depot_id"] = depot_id
                return from_metta
        df = self._chargers_df[self._chargers_df["depot_id"] == depot_id]
        chargers: List[Dict] = []
        for _, row in df.iterrows():
            chargers.append(
                {
                    "id": row["id"],
                    "depot_id": row["depot_id"],
                    "connector": row["connector"],
                    "max_kw": float(row["max_kw"]),
                }
            )
        return chargers

    def connectors_compatible(self, vehicle_connector: str, charger_connector: str) -> bool:
        return str(vehicle_connector).lower() == str(charger_connector).lower()

    def get_site_peak_limit_kw(self, depot_id: str) -> float:
        if depot_id in self._site_peak_override:
            return float(self._site_peak_override[depot_id])
        if self._use_metta and self.metta:
            val = self.metta.query_site_peak(depot_id)
            if val is not None:
                return float(val)
        df = self._site_limits_df[self._site_limits_df["depot_id"] == depot_id]
        if df.empty:
            return 60.0
        return float(df.iloc[0]["site_peak_kw"])  # kW

    def get_max_concurrent_chargers(self, depot_id: str) -> int:
        return len(self.get_depot_chargers(depot_id))

    def get_total_capacity_kw(self, depot_id: str) -> float:
        chargers = self.get_depot_chargers(depot_id)
        return sum(ch["max_kw"] for ch in chargers)

    # --- Runtime mutation helpers (what-if scenarios) ---
    def set_site_peak_limit_kw(self, depot_id: str, kw: float) -> None:
        self._site_peak_override[str(depot_id)] = float(kw)

    def add_blackout(self, depot_id: str, start_hour: int, end_hour: int) -> None:
        start = max(0, int(start_hour))
        end = max(start, int(end_hour))
        arr = self._blackouts.setdefault(str(depot_id), [])
        arr.append([start, end])

    def is_blackout(self, depot_id: str, hour: int) -> bool:
        windows = self._blackouts.get(str(depot_id), [])
        h = int(hour)
        for w in windows:
            if len(w) == 2 and w[0] <= h < w[1]:
                return True
        return False

    def clear_blackouts(self, depot_id: str | None = None) -> None:
        if depot_id is None:
            self._blackouts.clear()
        else:
            self._blackouts.pop(str(depot_id), None)

    def clear_site_peak_override(self, depot_id: str | None = None) -> None:
        if depot_id is None:
            self._site_peak_override.clear()
        else:
            self._site_peak_override.pop(str(depot_id), None)
