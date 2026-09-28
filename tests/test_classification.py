import pytest

from bpbot.services.classification import classify, is_urgent


@pytest.mark.parametrize(
    "sys, dia, expected",
    [
        (119, 79, "green"),
        (120, 79, "yellow"),
        (129, 79, "yellow"),
        (130, 79, "orange"),
        (139, 89, "orange"),
        (125, 85, "orange"),  # diastolic pushes it up from yellow
        (118, 80, "orange"),  # diastolic alone
        (140, 70, "red"),
        (145, 70, "red"),  # was a gap in the original rules
        (150, 85, "red"),  # was a gap in the original rules
        (120, 90, "red"),
        (180, 121, "red"),
    ],
)
def test_classify(sys, dia, expected):
    assert classify(sys, dia) == expected


def test_is_urgent():
    assert is_urgent(180, 100)
    assert is_urgent(150, 120)
    assert not is_urgent(179, 119)
