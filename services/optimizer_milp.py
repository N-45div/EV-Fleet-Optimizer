from typing import Dict, List, Tuple

from ortools.linear_solver import pywraplp


class OptimizerMILP:
    def __init__(self, kg, telemetry, prices):
        self.kg = kg
        self.telemetry = telemetry
        self.prices = prices

    def optimize(self, horizon_hours: int, objective: str = "cost") -> Dict:
        fleet = self.telemetry.get_fleet_state()["vehicles"]
        price_curve: List[float] = self.prices.get_prices(horizon_hours)

        vehicles_by_depot: Dict[str, List[Dict]] = {}
        for v in fleet:
            vehicles_by_depot.setdefault(v["depot_id"], []).append(v)

        chargers_by_depot: Dict[str, List[Dict]] = {}
        for depot_id in vehicles_by_depot.keys():
            chargers_by_depot[depot_id] = self.kg.get_depot_chargers(depot_id)

        solver = pywraplp.Solver.CreateSolver("SCIP")
        if solver is None:
            raise RuntimeError("ORTools SCIP solver not available")

        # Decision variables
        # x[v,c,h] in kW, z[v,c,h] in {0,1} to model assignment
        x: Dict[Tuple[str, str, int], pywraplp.Variable] = {}
        z: Dict[Tuple[str, str, int], pywraplp.Variable] = {}

        for depot_id, depot_vehicles in vehicles_by_depot.items():
            chargers = chargers_by_depot.get(depot_id, [])
            for v in depot_vehicles:
                v_id = v["id"]
                v_conn = str(v.get("connector", "")).upper()
                v_max = float(v.get("max_kw", 22.0))
                dep = int(v["departure_hour"])  # exclusive
                for h in range(min(horizon_hours, dep)):
                    if self.kg.is_blackout(depot_id, h):
                        continue
                    for ch in chargers:
                        c_id = str(ch["id"])
                        c_conn = str(ch.get("connector", "")).upper()
                        c_max = float(ch.get("max_kw", 22.0))
                        if v_conn and c_conn and v_conn != c_conn:
                            continue  # incompatible
                        ub = min(v_max, c_max)
                        if ub <= 0:
                            continue
                        x[(v_id, c_id, h)] = solver.NumVar(0.0, ub, f"x_{v_id}_{c_id}_{h}")
                        z[(v_id, c_id, h)] = solver.BoolVar(f"z_{v_id}_{c_id}_{h}")
                        # Link x and z
                        solver.Add(x[(v_id, c_id, h)] <= ub * z[(v_id, c_id, h)])

        # Vehicle demand constraints: sum_c,h x[v,c,h] >= required_kwh
        for v in fleet:
            v_id = v["id"]
            dep = int(v["departure_hour"])  # exclusive
            need = float(v["required_kwh"])  # 1h slots: kW == kWh per slot
            expr = solver.Sum(x.get((v_id, c_id, h), 0.0) for (vid, c_id, h) in x.keys() if vid == v_id and h < dep)
            solver.Add(expr >= need)

        # At most one charger per vehicle per hour
        for v in fleet:
            v_id = v["id"]
            dep = int(v["departure_hour"])  # exclusive
            for h in range(min(horizon_hours, dep)):
                expr = solver.Sum(z.get((v_id, c_id, h), 0.0) for (vid, c_id, hh) in z.keys() if vid == v_id and hh == h)
                if isinstance(expr, pywraplp.LinearExpr):
                    solver.Add(expr <= 1)

        # One vehicle per charger per hour
        for depot_id, chargers in chargers_by_depot.items():
            for ch in chargers:
                c_id = str(ch["id"])
                for h in range(horizon_hours):
                    if self.kg.is_blackout(depot_id, h):
                        # force zero
                        for v in vehicles_by_depot[depot_id]:
                            if (v["id"], c_id, h) in x:
                                solver.Add(x[(v["id"], c_id, h)] <= 0.0)
                                solver.Add(z[(v["id"], c_id, h)] <= 0.0)
                        continue
                    expr = solver.Sum(z.get((v["id"], c_id, h), 0.0) for v in vehicles_by_depot[depot_id])
                    if isinstance(expr, pywraplp.LinearExpr):
                        solver.Add(expr <= 1)

        # Depot/hour capacity
        for depot_id, depot_vehicles in vehicles_by_depot.items():
            site_peak = self.kg.get_site_peak_limit_kw(depot_id)
            total_capacity_kw = self.kg.get_total_capacity_kw(depot_id)
            hour_budget_kw = min(site_peak, total_capacity_kw)
            chargers = chargers_by_depot.get(depot_id, [])
            for h in range(horizon_hours):
                if self.kg.is_blackout(depot_id, h):
                    continue  # already zeroed above
                expr = solver.Sum(x.get((v["id"], ch["id"], h), 0.0) for v in depot_vehicles for ch in chargers)
                if isinstance(expr, pywraplp.LinearExpr):
                    solver.Add(expr <= hour_budget_kw)

        # Objective
        if objective == "peak":
            P = solver.NumVar(0.0, solver.infinity(), "peak_var")
            for depot_id, depot_vehicles in vehicles_by_depot.items():
                chargers = chargers_by_depot.get(depot_id, [])
                for h in range(horizon_hours):
                    expr = solver.Sum(x.get((v["id"], ch["id"], h), 0.0) for v in depot_vehicles for ch in chargers)
                    if isinstance(expr, pywraplp.LinearExpr):
                        solver.Add(expr <= P)
            cost_term = solver.Sum(price_curve[h] * x_var for ((_, _, h), x_var) in x.items())
            solver.Minimize(P + 0.001 * cost_term)
        else:
            solver.Minimize(solver.Sum(price_curve[h] * x_var for ((_, _, h), x_var) in x.items()))

        status = solver.Solve()
        if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
            raise RuntimeError("MILP did not find a feasible solution")

        # Extract solution
        per_vehicle: Dict[str, Dict[int, float]] = {}
        per_depot: Dict[str, Dict[int, float]] = {}
        # init per_depot
        for depot_id in vehicles_by_depot.keys():
            per_depot[depot_id] = {}

        for (v_id, c_id, h), var in x.items():
            val = var.solution_value()
            if val <= 1e-9:
                continue
            per_vehicle.setdefault(v_id, {})[h] = per_vehicle.get(v_id, {}).get(h, 0.0) + float(val)
            # find depot for charger
            depot_id = None
            for dep, chargers in chargers_by_depot.items():
                if any(str(ch["id"]) == str(c_id) for ch in chargers):
                    depot_id = dep
                    break
            if depot_id is not None:
                per_depot[depot_id][h] = per_depot[depot_id].get(h, 0.0) + float(val)

        # Explanations: top per-hour allocations
        items: List[Tuple[str, int, float]] = []
        for v_id, alloc in per_vehicle.items():
            for h, kw in alloc.items():
                items.append((v_id, h, kw))
        items.sort(key=lambda t: (-t[2], price_curve[t[1]] if t[1] < len(price_curve) else 0.0))
        explanations: List[str] = []
        for v_id, h, kw in items[:20]:
            explanations.append(f"{v_id} @h{h}: {kw:.1f}kW via MILP")

        # Remaining need approximation
        remaining_kwh: Dict[str, float] = {}
        for v in fleet:
            v_id = v["id"]
            need = float(v["required_kwh"]) - sum(per_vehicle.get(v_id, {}).values())
            remaining_kwh[v_id] = need

        return {
            "per_vehicle": per_vehicle,
            "per_depot": per_depot,
            "price_curve": price_curve,
            "explanations": explanations,
            "remaining_kwh": remaining_kwh,
        }
