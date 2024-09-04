from datetime import date, datetime, timedelta

import numpy as np
import pytz
import tintervals as ti


# smart start/stop interpretation
def parse_input_date(s):
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
    start = ti.mjd2datetime(start)
    stop = ti.mjd2datetime(stop)
    date_generated = [start + timedelta(days=-1) + timedelta(days=x) for x in range(0, (stop - start).days + 1)]
    return date_generated


def is_summer_time_changing_between(date1, date2):
    # https://stackoverflow.com/questions/69483502/is-there-a-way-to-infer-in-python-if-a-date-is-the-actual-day-in-which-the-dst
    # check for summertime change

    local_start = pytz.timezone("Europe/Rome").localize(date1)
    local_end = pytz.timezone("Europe/Rome").localize(date2)
    summertime_changed = local_start.tzinfo != local_end.tzinfo
    return summertime_changed


def today():
    return date.today().isoformat()
