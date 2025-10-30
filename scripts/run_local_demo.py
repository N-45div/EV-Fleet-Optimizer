import os
import sys

# Ensure project root is on sys.path so "services" imports work when running this file directly
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.telemetry_service import TelemetryService
from services.price_service import PriceService
from services.kg_service import KGService
from services.optimizer_service import OptimizerService
from services.evaluation_service import EvaluationService


def main():
    telemetry = TelemetryService()
    prices = PriceService()
    kg = KGService()
    optimizer = OptimizerService(kg=kg, telemetry=telemetry, prices=prices)
    eval_service = EvaluationService()

    horizon = 24
    # Objective selection via CLI or env
    objective = os.getenv("OBJECTIVE_DEFAULT", "cost").lower()
    if len(sys.argv) > 1:
        objective = sys.argv[1].lower()
    if objective not in ("cost", "peak"):
        objective = "cost"

    schedule = optimizer.optimize(horizon_hours=horizon, request_text="local demo run", objective=objective)
    kpis = eval_service.compute_kpis(schedule=schedule, price_curve=schedule["price_curve"])

    print("EV Fleet Charge Optimizer Demo\n---")
    print(f"Horizon: {horizon}h")
    print(f"Objective: {objective}")
    print(f"Total cost: ${kpis['total_cost']:.2f}")
    print(f"Peak power: {kpis['peak_kw']:.1f} kW")
    print(f"On-time compliance: {kpis['on_time_pct']:.1f}%")
    print("Top decisions:")
    for line in schedule.get("explanations", [])[:10]:
        print(" -", line)


if __name__ == "__main__":
    main()
