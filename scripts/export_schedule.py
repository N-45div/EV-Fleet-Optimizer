import os
import sys
import json

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

    horizon = int(os.getenv("HORIZON_HOURS", "24"))
    objective = os.getenv("OBJECTIVE_DEFAULT", "cost").lower()
    if objective not in ("cost", "peak"):
        objective = "cost"

    schedule = optimizer.optimize(horizon_hours=horizon, request_text="export", objective=objective)
    kpis = eval_service.compute_kpis(schedule=schedule, price_curve=schedule["price_curve"])

    out_dir = os.getenv("OUT_DIR", "./")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "schedule.json"), "w") as f:
        json.dump(schedule, f, indent=2)
    with open(os.path.join(out_dir, "kpis.json"), "w") as f:
        json.dump(kpis, f, indent=2)

    print(f"Wrote {os.path.join(out_dir, 'schedule.json')} and kpis.json")


if __name__ == "__main__":
    main()
