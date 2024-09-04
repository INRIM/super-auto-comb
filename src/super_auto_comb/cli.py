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
from super_auto_comb.deglitch import (
    deglitch_from_bounds,
    deglitch_from_double_counting,
    deglitch_from_f0,
    deglitch_from_median_filter,
)
from super_auto_comb.fix_files import find_files, fix_files
from super_auto_comb.load_files import genfromkk
from super_auto_comb.track_changes import (
    df_add_name,
    df_extract,
    df_fix_end,
    df_from_cirt,
    df_limit,
    df_merge,
    df_reduce,
    format_possibly_changing_info,
    load_do_setup,
)
from super_auto_comb.utils import generate_dates, parse_input_date

plt.close("all")
plt.ioff()


def parse_args(args):
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

    return parser.parse_args(args)


def cli():
    args = parse_args(sys.argv[1:])

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
    # setups for reading inputs and for saving outpus (tracks different changes)
    in_setups = []
    out_setups = []

    # bug: not enough circular t informaton if start is much later that the start in the setup
    # cirt = load_cirt_setup(start, stop)
    cirt = df_from_cirt(start - 40, stop)

    for do in do_bar:
        do_bar.set_description(f"Loading {do} setup.")
        df = load_do_setup(do, dir=args.setup_dir)
        df = df_merge(df, cirt)
        df = df_limit(df, start, stop)

        # start to worry here about what will be tracked changes
        # nominal frequency is ALWAYS tracked on the output
        tracked = ["nominal"]
        if args.track_phys:
            tracked += ["physical"]
        if args.track_comb:
            tracked += ["comb"]
        if args.track_maser:
            tracked += ["maser"]
        if args.track_cirt:
            tracked += ["cirt"]

        df_add_name(
            df,
            fix=["cirt"],
            var=[x for x in ["physical", "comb", "maser"] if x in tracked],
        )

        # output_df only has major changes tracked
        output_df = df_reduce(df, tracked)

        in_setups += [df]
        out_setups += [output_df]

    # LOOP 2: fix and find files based on date
    date_generated = generate_dates(start, stop)

    date_bar = tqdm(date_generated)
    files_to_be_processed = []

    for date in date_bar:
        date_bar.set_description(f"Checking {date.strftime('%Y-%m-%d')} files.")

        con_files = fix_files(args.comb_dir, date)

        for file in con_files:
            tqdm.write(f"Conflict resolved for {os.path.basename(file)}.")

        files_to_be_processed += find_files(args.comb_dir, date)

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

            do_setup = in_setups[doi]

            # LOOP 3c: track changes
            # pandas is stupid :(
            # 	for x in loyb[loyb['datetime']>59900].iloc:
            #  ...:     print(x['cirt'])
            for s in do_setup.iloc:
                if s["valid"] is False:
                    continue

                this_start = max(start, s["datetime"])
                this_stop = min(stop, s["datetime_end"])

                # mask data
                tstart = ti.mjd2epoch(this_start)
                tstop = ti.mjd2epoch(this_stop)

                datamask = (alldata[:, 0] >= tstart) & (alldata[:, 0] < tstop)
                data = alldata[datamask]

                if len(data) > 0:
                    comb = s["comb"]
                    nominal = s["nominal"]
                    N = s["N"]  # limit between start/stop
                    f_rep = s["frep_" + comb]
                    f0 = s["f0_" + comb]
                    f_beat_sign = s["fbeat_sign"]
                    k_scale = s["kscale"]
                    f0_scale = s["f0_scale"]
                    f_offset = s["foffset"]

                    columns = df_extract(s, ["counter", "counter1", "counter2"])
                    columns = np.atleast_1d(columns).astype(int)
                    bounds = (
                        df_extract(s, ["min", "min1", "min2"]),
                        df_extract(s, ["max", "max1", "max2"]),
                    )
                    los = df_extract(s, ["flo", "flo1", "flo2"])
                    if len(los) > 1:
                        threshold = s["threshold"]
                    else:
                        # threshold not needed, this is arbitrary as long as >0 (the output of np.ptp on a len 1 axis)
                        threshold = 1

                    median_window = args.median_filter_window
                    median_threshold = args.median_filter_threshold

                    red_data = data[:, columns]
                    f0_meas = data[:, s["counter_f0_" + comb]]
                    los = np.resize(np.asarray(los, dtype=float), columns.shape[0])
                    los_data = np.abs(red_data + los)
                    f_beat = np.mean(los_data, axis=-1)

                    # deglitch(alldata,  columns, bounds=(-np.inf, np.inf), los=0., threshold=0.2, glitch_ext=3, median_window=60, median_threshold=250.):
                    # f_beat, mask1, mask2, mask3, ptp = deglitch(
                    #     data,
                    #     columns,
                    #     bounds,
                    #     los,
                    #     threshold,
                    #     glitch_ext=3,
                    #     median_window=median_window,
                    #     median_threshold=median_threshold,
                    # )

                    mask1 = deglitch_from_bounds(red_data, bounds)

                    mask2 = deglitch_from_double_counting(los_data, threshold, glitch_ext=3)

                    mask3 = deglitch_from_f0(f0_meas, f0_nominal=s["f0_" + comb], threshold=0.25)

                    median_deglitch = True

                    tmask = mask1 & mask2 & mask3
                    if median_deglitch:
                        mask4 = deglitch_from_median_filter(
                            f_beat,
                            premask=tmask,
                            median_window=median_window,
                            median_threshold=median_threshold,
                        )
                        tmask = mask1 & mask2 & mask3 & mask4
                    else:
                        mask4 = np.ones_like(mask1).astype(bool)

                    flag = (tmask) * args.flag

                    # beat2y(f_beat,  nominal,  N, f_rep, f0, f_beat_sign=1, k_scale=1, f0_scale=1, f_offset=0.):
                    y = beat2y(f_beat, nominal, N, f_rep, f0, f_beat_sign, k_scale, f0_scale, f_offset)

                    out = np.column_stack((data[:, 0], y, flag))

                    # DONE, concatenate with previous data
                    data_out[doi] += [out]

                    mjd = ti.mjd_from_epoch(data[:, 0])

                    # Some Figure of merit
                    # * measurement of channel deviation
                    # sqrt<|diff between channels|^2>
                    # ch_dev = np.sqrt(np.mean(ptp[tmask] ** 2))

                    # f0 deviation
                    # f0_dev = np.mean(f0_diff[tmask])

                    # plot here
                    fig, axs = plt.subplots(3, sharex=True, figsize=(6.4 * 1.5, 4.8))
                    fig.suptitle(f"{basename} - {comb} - {do}")

                    axs[0].set_ylabel("Flag")
                    # axs[0].plot(mjd, flag, label=f'Removed points = {sum(flag==0)}')
                    axs[0].fill_between(mjd, 3 - mask1, 2, label=f"Filter mask -> {sum(~mask1)}", step="pre")
                    axs[0].fill_between(mjd, 2 - mask2, 1, label=f"Glitch mask -> {sum(~mask2)}", step="pre")
                    axs[0].fill_between(mjd, 1 - mask3, 0, label=f"f0 mask -> {sum(~mask3)}", step="pre")
                    axs[0].fill_between(mjd, 0 - mask4, -1, label=f"Median mask -> {sum(~mask4)}", step="pre")

                    axs[0].legend(loc="center left", bbox_to_anchor=(1, 0.5))
                    axs[1].plot(mjd, f_beat * 1e-6, label="raw")
                    axs[1].plot(mjd[flag > 0], f_beat[flag > 0] * 1e-6, ".", label=f"All masks -> {sum(flag==0)}")
                    axs[1].plot(mjd[~(mask2)], f_beat[~(mask2)] * 1e-6, "o", label="Glitches")
                    axs[1].set_ylabel("Beat /MHz")
                    axs[1].legend(loc="center left", bbox_to_anchor=(1, 0.5))

                    if sum(flag) > 0:
                        meany = np.mean(y[flag > 0])
                        axs[2].axhline(meany, label=f"Mean = {meany:.3}", color="black")

                    axs[2].plot(mjd[flag > 0], y[flag > 0], ".", label=f"Points = {sum(flag>0)}", color="C1")
                    # axs[2].plot(mjd[flag>0], uniform_filter1d(y[flag>0],1000), '.', label=f'Moving average')
                    axs[2].set_ylabel("y")
                    axs[2].set_xlabel("MJD")
                    axs[2].set_xlim(np.min(mjd), np.min(mjd) + 1)
                    axs[2].legend(loc="center left", bbox_to_anchor=(1, 0.5))

                    plt.tight_layout()
                    figdir = os.path.join(args.fig_dir, s["name"], do)

                    if not os.path.exists(figdir):
                        os.makedirs(figdir)
                    figname = os.path.join(figdir, basename + ".png")
                    plt.savefig(figname)

                    # bug: this leave a figure window hanging around.
                    # it does not seem necessary though since I called ioff()
                    # plt.close()

    # LOOP 4: save files
    # LOOP 4a: dos
    do_bar2 = tqdm(args.do)
    for doi, do in enumerate(do_bar2):
        do_bar2.set_description("Saving DO: " + do)

        do_out_setup = out_setups[doi].fillna("")
        do_in_setup = in_setups[doi].fillna("")

        out = np.concatenate(data_out[doi])

        # LOOP 4b: tracked changes
        for s in do_out_setup.iloc:
            if s["valid"] is False:
                continue

            this_start = max(start, s["datetime"])
            this_stop = min(stop, s["datetime_end"])

            # mask info
            infomask = (do_in_setup["datetime_end"] >= start) & (do_in_setup["datetime"] < stop)
            # note that ths_setup may have more lines for each do_out_setup
            this_setup = do_in_setup[infomask]

            # mask data
            tstart = ti.mjd2epoch(this_start)
            tstop = ti.mjd2epoch(this_stop)
            datamask = (out[:, 0] >= tstart) & (out[:, 0] < tstop)
            data = out[datamask]

            if datamask.any() & infomask.any():
                nominal = s["nominal"].strip("'")

                # TODO: descriptions are no longer used by rl.save_link_to_dir
                # I could use the "message" keyword instead
                HM = rl.Oscillator("INRIM_HM", "1")
                DO = rl.Oscillator("INRIM_" + do, nominal)

                dodesc = (
                    "Designed oscillator = "
                    + format_possibly_changing_info(this_setup, "physical")
                    + " measured on "
                    + format_possibly_changing_info(this_setup, "comb")
                )
                nom = "# Nominal frequency = " + nominal
                hm_desc = "# HM = " + format_possibly_changing_info(this_setup, "maser")
                message = "\n".join([dodesc, nom, hm_desc])

                link = rl.Link(data=out[datamask], oscA=DO, oscB=HM)
                link.drop_invalid()

                out_dir = os.path.join(args.dir, s["name"])
                rl.save_link_to_dir(out_dir, link, time_format=args.time_format, message=message)

    return True
