from datetime import date, datetime, timedelta

import numpy as np
import pytz
import tintervals as ti


# smart start/stop interpretation
def parse_input_date(s):
    """Smart interpretation of input date.
    Float input > 1 is interpreted as MJD.
    Float input <= 1 is interpreted as "day ago" (-1 = yesterday, 0 = today, 1 = tomorrow, etc...)
    Otherwise inputs are parsed as date YYYY-MM-DD.

    Parameters
    ----------
    s : str
        Input.

    Returns
    -------
    mjd : float
        date as MJD rounded to integer.
    """
    try:
        d = float(s)
    except ValueError:
        # cannot convert to float -> try date
        # round to the nearest integer MJD (probably quicker than messing up with timezones)
        d = np.round(ti.datetime2mjd(datetime.strptime(s, "%Y-%m-%d")))
        return d

    if d > 1:
        # large number -> MJD
        return d
    else:
        # negative, 0 or 1 -> previous days
        return np.floor(ti.datetime2mjd(datetime.today())) + d


def generate_dates(start, stop):
    """Generate dates from start and stop.

    Parameters
    ----------
    start : float
        Start date as MJD.
    stop : float
        Stop date as MJD.

    Returns
    -------
    list of Datetime

    """
    start = ti.mjd2datetime(start)
    stop = ti.mjd2datetime(stop)
    date_generated = [start + timedelta(days=-1) + timedelta(days=x) for x in range(0, (stop - start).days + 1)]
    return date_generated


def is_summer_time_changing_between(date1, date2, timezone="Europe/Rome"):
    """Check for summer time changes by comparing the timezone infos of two dates.

    Parameters
    ----------
    date1 : datetime
        First datetime.
    date2 : datetime
        Second datetime.
    timezone : str
        Timezone name, by default "Europe/Rome".

    Returns
    -------
    bool
        True if the two dates as different times.
    """
    # https://stackoverflow.com/questions/69483502/is-there-a-way-to-infer-in-python-if-a-date-is-the-actual-day-in-which-the-dst
    # check for summertime change

    local_start = pytz.timezone(timezone).localize(date1)
    local_end = pytz.timezone(timezone).localize(date2)
    summertime_changed = local_start.tzinfo != local_end.tzinfo
    return summertime_changed


def today():
    """Return today as YYYY-MM-DD"""
    return date.today().isoformat()
