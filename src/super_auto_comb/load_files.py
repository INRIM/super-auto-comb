from datetime import datetime

import numpy as np
import tintervals as ti
from tqdm import tqdm

from super_auto_comb.utils import is_summer_time_changing_between


def genfromkk(fname, fix_summer_time=False, max_columns=12, **kwargs):
    """Load a single kk file.
    Return regularized timetags, assuming data coming at regular intervals and at integer seconds.

    Parameters
    ----------
    fname : file or str
            File or filename to be read
    max_columns : int, optional
            max number of columns to read, by default 12
    fix_summer_time : bool, optional
            If true, it will try to fix discontinuities due to summer time (will not work with gaps in the data > 1 h, by default False

    Returns
    -------
    out : ndarray
            Data read.
    """
    alldata = np.genfromtxt(
        fname,
        delimiter=[17] + [22] * max_columns,
        skip_header=1,
        skip_footer=0,
        converters={0: ti.kk2epoch},
        invalid_raise=False,
        encoding="UTF-8",
        **kwargs,
    )

    # faster but breaks on   Measurement interval (re-)synchronized!
    # alldata = pd.read_csv(fname, sep='\s+', header=None, converters={0:ti.kk2epoch},  **kwargs)

    alldata = np.atleast_2d(alldata)

    # genfromtxt do not skip lines with wrong number of columns if delimiter is given as number of chars
    alldata = alldata[~np.isnan(alldata).any(axis=-1)]

    t = alldata[:, 0]

    # regularize timetags -- required if the K+K is not sync'd properly
    # this expect data coming regularly every 1 second
    # and assure timetags at integer seconds
    dt = np.diff(t)
    dt = np.around(dt)

    # If I want to fix summer time and I detect the change, then I have to close gaps in dt of 1 h
    if fix_summer_time:
        start = datetime.fromtimestamp(t[0])
        stop = datetime.fromtimestamp(t[-1])
        if is_summer_time_changing_between(start, stop):
            tqdm.write(f"{fname}: Trying to fix summertime.")
            dt = dt % 3600.0

    t0 = np.round(t[0])
    t2 = np.insert(np.cumsum(dt) + t0, 0, t0)

    dev = t2[-1] - t[-1]
    if dev > 0.5:
        tqdm.write(f"{fname}: Timetags regularization deviation {dev} s")
    # check tags
    uniq, idx, count = np.unique(t2, return_index=True, return_counts=True)
    if sum(count > 1) > 0:
        tqdm.write(f"{fname}: {sum(count>1)} not unique timetags!")
        t2 = t2[idx]
        alldata = alldata[idx]

    allt = t2
    alldata[:, 0] = allt

    return alldata
