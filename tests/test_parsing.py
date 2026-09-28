import pytest

from bpbot.services.parsing import ParsedReading, ParseError, parse_log_args


def test_valid():
    assert parse_log_args("120/80 99") == ParsedReading(120, 80, 99)


def test_spaces_around_slash():
    assert parse_log_args("  120 / 80   99 ") == ParsedReading(120, 80, 99)


@pytest.mark.parametrize(
    "bad",
    [
        "",  # nothing
        "120/80",  # missing pulse
        "abc/80 70",  # not numbers
        "120-80 70",  # wrong separator
        "120/80 70 5",  # extra value
        "1200/80 70",  # too many digits
        "80/120 70",  # systolic <= diastolic
        "120/80 10",  # pulse out of range
        "40/30 70",  # systolic out of range
    ],
)
def test_rejects_bad_input(bad):
    with pytest.raises(ParseError):
        parse_log_args(bad)
