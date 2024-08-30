import argparse
import decimal
import glob
import os
import os.path
import shutil
import sys
from datetime import date, datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import numpy.lib.recfunctions as rfn
import pandas as pd
import tintervals as ti
import tintervals.rocitlinks as rl
from tqdm import tqdm

from super_auto_comb.calc import beat2y
from super_auto_comb.deglitch import deglitch
from super_auto_comb.load_files import genfromkk
from super_auto_comb.track_changes import df_extract, load_cirt_setup, load_do_setup
from super_auto_comb.utils import generate_dates, parse_input_date

plt.close("all")
plt.ioff()


def cli():
    # fmt: off

    parser = argparse.ArgumentParser(description='Process Comb data files.', formatter_class=argparse.ArgumentDefaultsHelpFormatter) 


    parser.add_argument('--do', nargs='+', type=str,  help='Name(s) of designed oscillator to be processed') 


    parser.add_argument('--start',  help='Start date as Date (YYYY-MM-DD), MJD or -n previous days.', default='-1', type=str) 
    parser.add_argument('--stop',  help='Stop date as Date (YYYY-MM-DD), MJD or -n previous days.', default='1', type=str) 

    # change defaults ?
    parser.add_argument('--dir',  help='Directory for storing results', default='./Outputs') 
    parser.add_argument('--fig-dir',  help='Directory for storing figures', default='./Outputs/Figures') 


    default_comb_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Data')) 
    default_setup_dir = os.path.join(default_comb_dir, 'Setup') 
    parser.add_argument('--comb-dir',  help='Directory of comb data', default=default_comb_dir) 
    parser.add_argument('--setup-dir',  help='Directory of setup data (describes comb and designed oscillator setup)', default=default_setup_dir)

    parser.add_argument('--time-format', choices=['iso', 'mjd', 'unix'], help='Output time format',  default='mjd')

    parser.add_argument('--do-not-fix-summer-time', action='store_true', help='Will not attempt to fix summer time.')
    parser.add_argument('--median-filter-window', type=int, help='Number of points in the median filter', default=60)
    parser.add_argument('--median-filter-threshold', type=float, help='Median filter threshold', default=250.)

    parser.add_argument('--max-columns', type=int, help='Number of columns in the comb datafile', default=12)

    parser.add_argument('--operator', type=str, help='Person in charge of the analysis.', default='Marco Pizzocaro')
    parser.add_argument('--flag', type=int, help='Flag for confidence level (0 = Discarded, 1 = Experimental, 2 = Operational)', default=1)


    parser.add_argument('--track-phys', action='store_true', help='Track changes on the physical oscillator.')
    parser.add_argument('--track-maser', action='store_true', help='Track changes on the maser physical oscillator.')
    parser.add_argument('--track-comb', action='store_true', help='Track changes on the comb.')
    parser.add_argument('--track-cirt', action='store_true', help='Track changes of the Circular T month.')

    # fmt: on

    # command = sys.argv
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    if not os.path.exists(args.fig_dir):
        os.makedirs(args.fig_dir)

    if args.do:
        return main(args)


def main(args):
    start = parse_input_date(args.start)
    stop = parse_input_date(args.stop)

    # LOOP 1: load DOs info
    do_bar = tqdm(args.do)
    setups = []
    cirt = load_cirt_setup(start, stop)
    for do in do_bar:
        do_bar.set_description(f"Loading {do} setup.")
        df, valid_combs = load_do_setup(do, dir=args.setup_dir)
        df = pd.merge_ordered(df, cirt, on="datetime", how="outer", fill_method="ffill")

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

        # # limit between start/stop
        # also note valid comb criteria
        # I can apply it here after I calculated datetime_ends
        mask = (
            (df["datetime_end"] >= start)
            & (df["datetime"] < stop)
            & (df["comb"].isin(valid_combs))
        )
        df = df[mask]

        setups += [df]

    date_generated = generate_dates(start, stop)

    # LOOP 2: fix files
    date_bar = tqdm(date_generated)
    files_to_be_processed = []

    for date in date_bar:
        date_bar.set_description(f"Checking {date.strftime('%Y-%m-%d')} files.")
        test = date.strftime("%y%m%d_?_Frequ.txt")
        files = [
            os.path.basename(_) for _ in glob.glob(os.path.join(args.comb_dir, test))
        ]

        # Pcloud may have conflicted files
        test = date.strftime("%y%m%d_?_Frequ (conflicted).txt")
        con_files = [
            os.path.basename(_) for _ in glob.glob(os.path.join(args.comb_dir, test))
        ]

        for con_name in con_files:
            good_name = con_name.replace(" (conflicted)", "")
            temp_name = "wasconflicted_" + good_name

            # backup of original file
            if good_name in files:
                shutil.copy2(
                    os.path.join(args.comb_dir, good_name),
                    os.path.join(args.comb_dir, temp_name),
                )
            else:
                files += [good_name]

            tqdm.write(f"Conflict resolved for {con_name} {good_name}.")

            # rename conflicted file to normal name (conflicted file has all the data)
            shutil.move(
                os.path.join(args.comb_dir, con_name),
                os.path.join(args.comb_dir, good_name),
            )

        files_to_be_processed += files

    files_to_be_processed.sort()

    # LOOP 3: read and process files
    data_out = [[] for d in args.do]
    file_bar = tqdm(files_to_be_processed)
    # LOOP 3a: files
    for fili in file_bar:
        basename = os.path.basename(fili)[:-4]

        file_bar.set_description("Processing " + basename)

        fname = os.path.join(args.comb_dir, fili.strip("\n"))
        alldata = genfromkk(
            fname,
            fix_summer_time=not args.do_not_fix_summer_time,
            max_columns=args.max_columns,
        )

        # LOOP 3b: dos
        for doi, do in enumerate(do_bar):
            do_bar.set_description("DO: " + do)

            do_setup = setups[doi]

            # LOOP 3c: track changes
            # pandas is stupid :(
            # 	for x in loyb[loyb['datetime']>59900].iloc:
            #  ...:     print(x['cirt'])
            for s in do_setup.iloc:
                this_start = max(start, s["datetime"])
                this_stop = min(stop, s["datetime_end"])

                # mask data
                tstart = ti.mjd2epoch(this_start)
                tstop = ti.mjd2epoch(this_stop)

                datamask = (alldata[:, 0] >= tstart) & (alldata[:, 0] < tstop)
                data = alldata[datamask]

                if len(data) > 0:
                    columns = df_extract(s, ["counter", "counter1", "counter2"])
                    bounds = (
                        df_extract(s, ["min", "min1", "min2"]),
                        df_extract(s, ["max", "max1", "max2"]),
                    )
                    los = df_extract(s, ["flo", "flo1", "flo2"])
                    threshold = s["threshold"]
                    median_window = args.median_filter_window
                    median_threshold = args.median_filter_threshold

                    # deglitch(alldata,  columns, bounds=(-np.inf, np.inf), los=0., threshold=0.2, glitch_ext=3, median_window=60, median_threshold=250.):
                    fbeat, mask1, mask2, mask3 = deglitch(
                        data,
                        columns,
                        bounds,
                        los,
                        threshold,
                        glitch_ext=3,
                        median_window=median_window,
                        median_threshold=median_threshold,
                    )

                    flag = mask1 & mask2 & mask3

                    comb = s["comb"]
                    nominal = s["nominal"]
                    N = s["N"]  # limit between start/stop
                    frep = s["frep_" + comb]
                    f0 = s["f0_" + comb]
                    fbeat_sign = s["fbeat_sign"]
                    kscale = s["kscale"]
                    f0_scale = s["f0_scale"]
                    foffset = s["foffset"]
                    # beat2y(fbeat,  nominal,  N, frep, f0, fbeat_sign=1, kscale=1, f0_scale=1, foffset=0.):
                    y = beat2y(
                        fbeat,
                        nominal,
                        N,
                        frep,
                        f0,
                        fbeat_sign,
                        kscale,
                        f0_scale,
                        foffset,
                    )

                    out = np.column_stack((data[:, 0], y, flag))

                    # DONE, concatenate with previous data
                    data_out[doi] += [out]

    # LOOP 4: save files
    # LOOP 4a: dos
    do_bar2 = tqdm(args.do)
    for doi, do in enumerate(do_bar2):
        do_bar2.set_description("Saving DO: " + do)

        do_setup = setups[doi].fillna("")

        # nominal frequency is ALWAYS tracked on the ouput
        tracked = ["nominal"]

        if args.track_phys:
            tracked += ["physical"]
        if args.track_comb:
            tracked += ["comb"]
        if args.track_maser:
            tracked += ["maser"]
        if args.track_cirt:
            tracked += ["cirt"]

        # PANDAS SUCKS!!!!
        # to avoid random SettingWithCopyWarning while inserting end_datetime and names I have to use a copy here !?!?
        # warning are raised (sometimes, maybe if tracked_setup is single row?) while seeting the edn_datetime or the new name
        tracked_setup = do_setup.drop_duplicates(subset=tracked, keep="first").copy()

        # fix end
        # inf for last point
        tracked_setup["datetime_end"] = tracked_setup["datetime"].shift(
            -1, fill_value=np.inf
        )

        # some machinery to get meaningful folder name
        # I want cirt first
        tracked.reverse()
        # get only significant info
        named = tracked_setup[tracked]
        # keep only columns where something did indeed changed
        keep = [c for c in named if len(named[c].unique()) > 1]
        if args.track_cirt and "cirt" not in keep:
            keep = ["cirt"] + keep

        named = named[keep]
        tracked_setup["name"] = named.agg("-".join, axis=1)

        out = np.concatenate(data_out[doi])

        # LOOP 4b: tracked changes
        for s in tracked_setup.iloc:
            this_start = max(start, s["datetime"])
            this_stop = min(stop, s["datetime_end"])

            # mask info
            infomask = (df["datetime_end"] >= start) & (df["datetime"] < stop)
            this_setup = do_setup[infomask]

            # mask data
            tstart = ti.mjd2epoch(this_start)
            tstop = ti.mjd2epoch(this_stop)
            datamask = (out[:, 0] >= tstart) & (out[:, 0] < tstop)
            data = out[datamask]

            if datamask.any() & infomask.any():
                # format possibly changing info
                def fpci(key):
                    uni = this_setup[key].unique()
                    what = "/".join(uni)

                    return what

                nominal = s["nominal"].strip("'")

                # TODO: descriptions are no longer used by rl.save_link_to_dir
                # I could use the "message" keyword instead
                HM = rl.Oscillator("INRIM_HM", "1")
                DO = rl.Oscillator("INRIM_" + do, nominal)

                dodesc = (
                    "Designed oscillator = "
                    + fpci("physical")
                    + " measured on "
                    + fpci("comb")
                )
                nom = "# Nominal frequency = " + nominal
                hmdesc = "# HM = " + fpci("maser")
                message = "\n".join([dodesc, nom, hmdesc])

                link = rl.Link(data=out[datamask], oscA=DO, oscB=HM)

                out_dir = os.path.join(args.dir, s["name"])
                rl.save_link_to_dir(
                    out_dir, link, time_format=args.time_format, message=message
                )
