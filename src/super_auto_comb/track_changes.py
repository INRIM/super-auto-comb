"""
This sub-package works with Pandas Dataframes whose first column is 'datetime'.
They are interpreted as setup description (frequency, counter channels, etc..) from the given datetime to the datetime on the next row.
These dataframes can me manipulated (loaded, merged, reduced, etc...) to keep track of only a subset of columns.
For loading inputs, all changes are tracked (e.g., I need to know when a counter channel is changed).
Outputs are instead customizable (e.g., I may or may not want to separate data based on which comb is used).
A colum 'name' can be added to describe each row based on some columns.
A column 'datetime_end' is always added to be equal to the datetime in the next row.

"""

import os

import numpy as np
import pandas as pd
import tintervals as ti

# track_changes works with pandas dataframes whose first column is 'datetime'.
# they are interpreted as setup description (frequency, counter channels, etc..) from the given datetime to the datetime on the next row.
# These dataframes can me manipulated (loaded, merged, reduced, etc...) to keep track of only a subset of columns.
# For loading inputs, all changes are tracked (e.g., I need to know when a counter channel is changed).
# Outputs are customizable (e.g., I may or may not want to separate data based on which comb is used).
# A colum 'name' can be added to describe each row based on some columns.
# A column 'datetime_end' is always added to be equal to the datetime in the next row.


def df_merge(df1, df2):
    """Merge two Dataframes tracking changes from both."""
    # merge_ordered + 'ffill' does what I need to track changes
    df = pd.merge_ordered(df1, df2, on="datetime", how="outer", fill_method="ffill")
    df_fix_end(df)
    return df


def df_fix_end(df):
    """Update or create the datetime_end column of the Dataframe to be the datetime of the following line (or np.inf)"""
    df["datetime_end"] = df["datetime"].shift(-1, fill_value=np.inf)


def df_reduce(df, subset):
    """Return a new df with changes only tracked in the subset columns."""
    tracked_df = df.drop_duplicates(subset=subset, keep="first").copy()
    df_fix_end(tracked_df)

    return tracked_df


def df_extract(df, cols):
    """Extract columns from a DataFrame OR Series ignoring columns that do not exists"""
    valid_cols = [c for c in cols if c in df]

    return list(df[valid_cols])


def df_add_name(df, fix, var=[]):
    """Add a name column to the Dataframe based on certain columns.
    Columns in fix will always be recorded in the name.
    Columns in var will be recorded only if some change is observed.
    """
    # reverse usually provide better ordering
    fix.reverse()
    var.reverse()

    if len(var) > 0:
        sub_df = df[var]
        keep = [c for c in var if len(sub_df[c].unique()) > 1]

        track = fix + keep
    else:
        track = fix

    # TODO: column may not be str
    sub_df = df[track].fillna("")
    df["name"] = sub_df.agg("-".join, axis=1)


def df_load(file):
    """Load a Dataframe from a file. The first column in the file should be a ISO datetime."""
    # two step file loading to have both the first header line and comments starting with #
    headers = pd.read_csv(file, sep="\t", nrows=1).columns.str.strip(" #")
    df = pd.read_csv(file, sep="\t", converters={0: ti.iso2mjd}, comment="#", header=None, names=headers)
    # remove whitespaces and # from column names
    # df.columns = df.columns.str.strip(" #")

    df_fix_end(df)

    return df


def df_limit(df, start, stop):
    """mask the Dataframe from start to stop."""
    df_fix_end(df)
    mask = (df["datetime_end"] >= start) & (df["datetime"] < stop)
    return df[mask]


def load_do_setup(do, dir):
    """Load DO and Comb setups. Use Pandas for some magic in keeping track of changes.

    Parameters
    ----------
    do : str
            DO name
    dir : str, optional
            working directory, by default ''


    Returns
    -------
    df
            Pandas dataframe with DO and Combs tracked changes.

    Note
    ----
    Load DO setups, combining it with comb setups (e.g., so if a DO has been measured with both comb1 and comb2, data is populated automatically).

    """
    do_file = os.path.join(dir, do + ".dat")

    df = df_load(do_file)

    # load comb setup
    combs = df["comb"].dropna().unique()
    valid_combs = []

    for comb in combs:
        combfile = os.path.join(dir, comb + ".dat")
        try:
            cdf = df_load(combfile)
        except FileNotFoundError:
            continue

        # rename columns
        mark = {x: (x + "_" + comb) for x in cdf.columns if x != "datetime"}
        cdf.rename(columns=mark, inplace=True)

        df = df_merge(df, cdf)
        valid_combs += [comb]

    # add comb-agnostic maser column
    def fun(row):
        if row["comb"] in valid_combs:
            return row["maser_" + row["comb"]]
        else:
            return np.nan

    df["maser"] = df.apply(fun, axis=1)

    # valid column
    def fun(row):
        return row["comb"] in valid_combs

    df["valid"] = df.apply(fun, axis=1)

    df_fix_end(df)

    return df


def df_from_cirt(start, stop):
    """Return a Dataframe tracking changes in Circular T number."""
    cirt_start, cirt_stop = ti.cirtvals(start, stop).T
    cirt_labels = ["{}-{:02d}".format(*ti.mjd2cirt(x)) for x in cirt_start]
    return pd.DataFrame({"datetime": cirt_start, "cirt": cirt_labels})


# format possibly changing info
# A column tracked for changes will always have a unique value associated for each row of inputs and outputs df.
# Columns not tracked for changes may have more rows in in the input df than in the output df
def format_possibly_changing_info(df, key):
    """Return a single string from values in a Dataframe column that may be one or more."""
    uni = df[key].unique()
    what = "/".join(uni)

    return what
