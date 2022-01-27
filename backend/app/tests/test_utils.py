""" Tests of app.utils"""

import datetime as dt

import pytest

import app.utils as ut


@pytest.fixture
def init_data_tests_db() -> None:
    """
    Override this session scoped autouse async fixture to avoid pytest async warnings
    """
    pass


def test_add_time() -> None:
    date = dt.date(2022, 1, 25)
    time = dt.time(12, 30)
    assert ut.add_time(date, time, minutes_to_add=30) == dt.time(13)
    assert ut.add_time(date, time, minutes_to_add=300) == dt.time(17, 30)


def test_subtract_time() -> None:
    date = dt.date(2022, 1, 25)
    time = dt.time(12, 30)
    assert ut.subtract_time(date, time, minutes_to_subtract=30) == dt.time(12)
    assert ut.subtract_time(date, time, minutes_to_subtract=300) == dt.time(7, 30)


def test_from_weekday_int_to_str() -> None:
    with pytest.raises(AssertionError):
        ut.from_weekday_int_to_str(7)
    assert ut.from_weekday_int_to_str(0) == "monday"
    assert ut.from_weekday_int_to_str(1) == "thursday"
    assert ut.from_weekday_int_to_str(2) == "wednesday"
    assert ut.from_weekday_int_to_str(3) == "tuesday"
    assert ut.from_weekday_int_to_str(4) == "friday"
    assert ut.from_weekday_int_to_str(5) == "saturday"
    assert ut.from_weekday_int_to_str(6) == "sunday"
