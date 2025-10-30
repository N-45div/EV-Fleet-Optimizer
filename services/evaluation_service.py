from typing import Dict, List


class EvaluationService:
    def compute_kpis(self, schedule: Dict, price_curve: List[float]) -> Dict[str, float]:
        per_vehicle: Dict[str, Dict[int, float]] = schedule.get("per_vehicle", {})
        per_depot: Dict[str, Dict[int, float]] = schedule.get("per_depot", {})
        remaining_kwh: Dict[str, float] = schedule.get("remaining_kwh", {})

        # Total cost = sum over hours (sum vehicle kW) * price[$/kWh]
        max_hour = 0
        for v_id, alloc in per_vehicle.items():
            if alloc:
                max_hour = max(max_hour, max(alloc.keys()))
        horizon = min(len(price_curve), max_hour + 1) if price_curve else (max_hour + 1)

        total_cost = 0.0
        for h in range(horizon):
            hour_kw = sum(alloc.get(h, 0.0) for alloc in per_vehicle.values())
            price = price_curve[h] if h < len(price_curve) else price_curve[-1]
            total_cost += hour_kw * price

        # Peak kW across all depots
        peak_kw = 0.0
        for h in range(horizon):
            total_kw_h = 0.0
            for depot_id, alloc in per_depot.items():
                total_kw_h += alloc.get(h, 0.0)
            if total_kw_h > peak_kw:
                peak_kw = total_kw_h

        # On-time compliance: % vehicles with remaining_kwh <= 0 (met demand)
        total_vehicles = len(remaining_kwh) if remaining_kwh else len(per_vehicle)
        met = 0
        for v_id, rem in remaining_kwh.items():
            if rem <= 1e-6:
                met += 1
        on_time_pct = 100.0 * (met / total_vehicles) if total_vehicles > 0 else 100.0

        return {
            "total_cost": float(total_cost),
            "peak_kw": float(peak_kw),
            "on_time_pct": float(on_time_pct),
        }
