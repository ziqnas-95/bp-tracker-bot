from bpbot.services.analytics import compute_monthly_average


def test_no_readings_returns_none():
    assert compute_monthly_average([]) is None


def test_average_of_multiple_readings():
    rows = [
        {"systolic": 120, "diastolic": 80, "pulse": 70},
        {"systolic": 130, "diastolic": 90, "pulse": 74},
    ]
    avg = compute_monthly_average(rows)
    assert avg.count == 2
    assert avg.avg_systolic == 125
    assert avg.avg_diastolic == 85
    assert avg.avg_pulse == 72
