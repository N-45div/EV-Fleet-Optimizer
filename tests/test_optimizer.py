from services.telemetry_service import TelemetryService
from services.price_service import PriceService
from services.kg_service import KGService
from services.optimizer_service import OptimizerService


def test_greedy_optimizer_produces_schedule():
    telemetry = TelemetryService()
    prices = PriceService()
    kg = KGService()
    opt = OptimizerService(kg=kg, telemetry=telemetry, prices=prices)

    schedule = opt.optimize(horizon_hours=24)

    assert "per_vehicle" in schedule
    assert "per_depot" in schedule
    assert len(schedule["price_curve"]) == 24
    # no negative allocations
    for alloc in schedule["per_vehicle"].values():
        for v in alloc.values():
            assert v >= 0
