from typing import Dict, List, Tuple


class OptimizerService:
    def __init__(self, kg, telemetry, prices):
        self.kg = kg
        self.telemetry = telemetry
        self.prices = prices

    def optimize(self, horizon_hours: int, request_text: str = "", objective: str = "cost") -> Dict:
        fleet = self.telemetry.get_fleet_state()["vehicles"]
        price_curve: List[float] = self.prices.get_prices(horizon_hours)

        vehicles_by_depot: Dict[str, List[Dict]] = {}
        for v in fleet:
            vehicles_by_depot.setdefault(v["depot_id"], []).append(v)

        price_order: List[Tuple[int, float]] = sorted(
            [(h, p) for h, p in enumerate(price_curve)], key=lambda x: x[1]
        )

        per_vehicle: Dict[str, Dict[int, float]] = {}
        per_depot: Dict[str, Dict[int, float]] = {}
        explanations: List[str] = []

        remaining_kwh: Dict[str, float] = {v["id"]: float(v["required_kwh"]) for v in fleet}

        for depot_id, depot_vehicles in vehicles_by_depot.items():
            per_depot[depot_id] = {}

        if objective == "peak":
            # Peak-aware heuristic: for each depot, allocate each vehicle to the hours with lowest current depot load first,
            # breaking ties by cheaper price.
            for depot_id, depot_vehicles in vehicles_by_depot.items():
                site_peak = self.kg.get_site_peak_limit_kw(depot_id)
                total_capacity_kw = self.kg.get_total_capacity_kw(depot_id)
                max_sessions = self.kg.get_max_concurrent_chargers(depot_id)
                sessions_map: Dict[int, int] = {}

                # Sort vehicles by earliest departure, then largest need
                depot_vehicles_sorted = sorted(
                    depot_vehicles,
                    key=lambda v: (int(v["departure_hour"]), -remaining_kwh[v["id"]]),
                )

                for v in depot_vehicles_sorted:
                    v_id = v["id"]
                    need = remaining_kwh[v_id]
                    v_max = float(v.get("max_kw", 22.0))
                    dep = int(v["departure_hour"])
                    if need <= 0:
                        continue

                    # Iteratively allocate across hours from lowest-load → higher
                    while need > 1e-6:
                        # Build hour list for this vehicle respecting departure
                        hours = [h for h in range(horizon_hours) if h < dep]
                        if not hours:
                            break
                        # Sort hours by (current depot load, price) and skip blackout windows
                        hours = [h for h in hours if not self.kg.is_blackout(depot_id, h)]
                        hours.sort(key=lambda h: (per_depot[depot_id].get(h, 0.0), price_curve[h]))
                        allocated_this_round = False
                        for hour in hours:
                            hour_budget_kw = min(site_peak, total_capacity_kw)
                            current = per_depot[depot_id].get(hour, 0.0)
                            if current >= hour_budget_kw:
                                continue

                            # Approximate sessions constraint by limiting per-hour allocations count
                            # (we don't track sessions per connector; for MVP this is acceptable)
                            if sessions_map.get(hour, 0) >= max_sessions:
                                continue
                            # Allocate up to v_max while respecting depot budget.
                            grant = min(v_max, need, hour_budget_kw - current)
                            if grant <= 0:
                                continue
                            per_vehicle.setdefault(v_id, {})[hour] = per_vehicle.get(v_id, {}).get(hour, 0.0) + grant
                            per_depot[depot_id][hour] = current + grant
                            remaining_kwh[v_id] -= grant
                            need -= grant
                            sessions_map[hour] = sessions_map.get(hour, 0) + 1
                            allocated_this_round = True
                            if len(explanations) < 20:
                                explanations.append(
                                    f"{v_id} @h{hour}: {grant:.1f}kW for peak-flattening (current depot h{hour}={per_depot[depot_id][hour]:.1f}kW, price=${price_curve[hour]:.2f})"
                                )
                            # Move to next hour after one grant to spread load
                            break
                        if not allocated_this_round:
                            break
        else:
            # Cost objective (default): process hours by ascending price
            for hour, price in price_order:
                for depot_id, depot_vehicles in vehicles_by_depot.items():
                    # Skip blackout windows at depot-hour
                    if self.kg.is_blackout(depot_id, hour):
                        continue
                    site_peak = self.kg.get_site_peak_limit_kw(depot_id)
                    total_capacity_kw = self.kg.get_total_capacity_kw(depot_id)
                    hour_budget_kw = min(site_peak, total_capacity_kw)
                    max_sessions = self.kg.get_max_concurrent_chargers(depot_id)

                    candidates = [
                        v for v in depot_vehicles
                        if remaining_kwh[v["id"]] > 0 and hour < int(v["departure_hour"]) and v.get("connector")
                    ]

                    candidates.sort(key=lambda v: (int(v["departure_hour"]), remaining_kwh[v["id"]]), reverse=False)

                    sessions = 0
                    allocated_kw_this_hour = 0.0

                    for v in candidates:
                        if sessions >= max_sessions or allocated_kw_this_hour >= hour_budget_kw:
                            break

                        v_id = v["id"]
                        v_max = float(v.get("max_kw", 22.0))
                        need = remaining_kwh[v_id]
                        if need <= 0:
                            continue

                        grant = min(v_max, need, hour_budget_kw - allocated_kw_this_hour)
                        if grant <= 0:
                            continue

                        per_vehicle.setdefault(v_id, {})[hour] = per_vehicle.get(v_id, {}).get(hour, 0.0) + grant
                        per_depot[depot_id][hour] = per_depot[depot_id].get(hour, 0.0) + grant
                        remaining_kwh[v_id] -= grant
                        allocated_kw_this_hour += grant
                        sessions += 1

                        if len(explanations) < 20:
                            explanations.append(
                                f"{v_id} @h{hour}: {grant:.1f}kW due to low price ${price:.2f}, departs h{int(v['departure_hour'])}"
                            )

        return {
            "per_vehicle": per_vehicle,
            "per_depot": per_depot,
            "price_curve": price_curve,
            "explanations": explanations,
            "remaining_kwh": remaining_kwh,
        }
