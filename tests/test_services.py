from services.price_service import PriceService


def test_price_curve_length_and_bounds():
    prices = PriceService()
    curve = prices.get_prices(24)
    assert len(curve) == 24
    for p in curve:
        assert 0.0 < p < 1.0
