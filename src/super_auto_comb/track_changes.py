import os

import pandas as pd
import tintervals as ti


def load_do_setup(do, dir=""):
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
    valid_combs
            List of valid comb names.
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

    return df, valid_combs


def df_extract(df, cols):
    """Extract columns from a DataFrame OR Series ignoring columns that do not exists"""
    valid_cols = [c for c in cols if c in df]
    return list(df[valid_cols])


def load_cirt_setup(start, stop):
    cirt_start, cirt_stop = ti.cirtvals(start, stop).T
    cirt_labels = ["{}-{:02d}".format(*ti.mjd2cirt(x)) for x in cirt_start]
    return pd.DataFrame({"datetime": cirt_start, "cirt": cirt_labels})
