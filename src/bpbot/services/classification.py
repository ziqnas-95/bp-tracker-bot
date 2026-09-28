from typing import Literal

Category = Literal["green", "yellow", "orange", "red"]


def classify(systolic: int, diastolic: int) -> Category:
    """Return the BP category. Checked from most to least severe, so the
    higher of the two numbers decides the result and nothing falls through."""
    if systolic >= 140 or diastolic >= 90:
        return "red"
    if systolic >= 130 or diastolic >= 80:
        return "orange"
    if systolic >= 120:  # diastolic is already known to be < 80 here
        return "yellow"
    return "green"


def is_urgent(systolic: int, diastolic: int) -> bool:
    """Very high range: the reply should tell the user to seek medical attention."""
    return systolic >= 180 or diastolic >= 120
