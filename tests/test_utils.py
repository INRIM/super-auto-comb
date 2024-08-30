from datetime import datetime

from super_auto_comb.utils import is_summer_time_changing_between


def test_is_summer_time_changing_between():
    assert (
        is_summer_time_changing_between(datetime(2024, 7, 1), datetime(2024, 8, 1))
        is False
    )
    assert (
        is_summer_time_changing_between(datetime(2023, 10, 1), datetime(2023, 11, 1))
        is True
    )
