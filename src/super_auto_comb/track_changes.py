import os

import numpy as np
import pandas as pd
import tintervals as ti


def load_simple_do_setup(do, dir="", add=None):
    """Load a simple DO setups. Use Pandas for some magic in keeping track of changes.

    Parameters
    ----------
    do : str
            DO name
    dir : str, optional
            working directory, by default ''
    add : Dataframe
            data to be merged when tracking changes (e.g., from load_cirt_setup())

    Returns
    -------
    df
            Pandas dataframe with DO tracked changes.

    """
    do_file = os.path.join(dir, do + ".dat")

    df = pd.read_csv(do_file, sep="\t", converters={0: ti.iso2mjd})
    # remove whitespaces and # from column names
    df.columns = df.columns.str.strip(" #")

    if add is not None:
        df = pd.merge_ordered(df, add, on="datetime", how="outer", fill_method="ffill")

    # track also end
    # inf for last point
    df["datetime_end"] = df["datetime"].shift(-1, fill_value=np.inf)

    return df


def load_do_setup(do, dir="", add=None, start=-np.inf, stop=np.inf):
    """Load DO and Comb setups. Use Pandas for some magic in keeping track of changes.

    Parameters
    ----------
    do : str
            DO name
    dir : str, optional
            working directory, by default ''
    add : Dataframe
            data to be merged when tracking changes (e.g., from load_cirt_setup())
    start: float
            start time limit
    stop: float
            stop time limit


    Returns
    -------
    df
            Pandas dataframe with DO and Combs tracked changes.

    valid_combs
            List of valid (=with specified setup) comb names.
    """
    do_file = os.path.join(dir, do + ".dat")

    df = pd.read_csv(do_file, sep="\t", converters={0: ti.iso2mjd})
    # remove whitespaces and # from column names
    df.columns = df.columns.str.strip(" #")

    # load comb setup
    combs = df["comb"].dropna().unique()
    valid_combs = []

    for comb in combs:
        combfile = os.path.join(dir, comb + ".dat")
        try:
            cdf = pd.read_csv(combfile, sep="\t", converters={0: ti.iso2mjd})
        except:
            continue

        # remove whitespaces and # from column names
        cdf.columns = cdf.columns.str.strip(" #")

        # rename columns
        mark = {x: (x + "_" + comb) for x in cdf.columns if x != "datetime"}
        cdf.rename(columns=mark, inplace=True)

        # merge_ordered + 'ffill' does what I need to track changes
        df = pd.merge_ordered(df, cdf, on="datetime", how="outer", fill_method="ffill")
        valid_combs += [comb]

    if add is not None:
        df = pd.merge_ordered(df, add, on="datetime", how="outer", fill_method="ffill")

    # track also end
    # inf for last point
    df["datetime_end"] = df["datetime"].shift(-1, fill_value=np.inf)

    # comb-agnostic maser column
    def fun(row):
        if row["comb"] in valid_combs:
            return row["maser_" + row["comb"]]
        else:
            return np.nan

    df["maser"] = df.apply(fun, axis=1)

    # limit between start/stop
    # also note valid comb criteria
    # I can apply it here after I calculated datetime_ends
    mask = (
        (df["datetime_end"] >= start)
        & (df["datetime"] < stop)
        & (df["comb"].isin(valid_combs))
    )
    df = df[mask]

    return df


def df_extract(df, cols):
    """Extract columns from a DataFrame OR Series ignoring columns that do not exists"""
    valid_cols = [c for c in cols if c in df]
    return list(df[valid_cols])


def load_cirt_setup(start, stop):
    cirt_start, cirt_stop = ti.cirtvals(start, stop).T
    cirt_labels = ["{}-{:02d}".format(*ti.mjd2cirt(x)) for x in cirt_start]
    return pd.DataFrame({"datetime": cirt_start, "cirt": cirt_labels})


def df_track(df, tracked, track_cirt=True):
    # PANDAS SUCKS!!!!
    # to avoid random SettingWithCopyWarning while isnerting end_datetime and names I have to use a copy here !?!?
    # warning are raised (sometimes, maybe if tracked_setup is single row?) while seeting the edn_datetime or the new name
    # at least moved in a function makes some sense
    tracked_df = df.drop_duplicates(subset=tracked, keep="first").copy()

    # fix end
    # inf for last point
    tracked_df["datetime_end"] = tracked_df["datetime"].shift(-1, fill_value=np.inf)

    df_add_name(tracked_df, tracked, track_cirt)

    return tracked_df


def df_add_name(df, tracked, track_cirt=True):
    # some machinery to get meaningful folder name
    # I want cirt first
    tracked.reverse()
    # get only significant info
    named = df[tracked]
    # keep only columns where something did indeed change
    keep = [c for c in named if len(named[c].unique()) > 1]
    if track_cirt and "cirt" not in keep:
        keep = ["cirt"] + keep

    # store the name for both in and out setups
    named = named[keep]
    df["name"] = named.agg("-".join, axis=1)
