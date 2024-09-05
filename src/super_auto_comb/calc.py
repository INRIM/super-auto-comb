import decimal

import numpy as np


def beat2y(f_beat, nominal, N, f_rep, f0, f_beat_sign=1, k_scale=1, f0_scale=1, f_offset=0.0):
    """Calculate the fractional frequency y from beatnote values, using arbitrary precision numbers where appropriate.

    Parameters
    ----------
    f_beat : ndarray of floats
        Input frequency beat, unsigned
    nominal : str
        Nominal frequency in Hz as string.
    N : int
        Comb tooth number
    f_rep : float
        Comb repetition rate in Hz
    f0 : float
        Comb offset frequency in Hz
    f_beat_sign : int, optional
        Sign of f_beat, by default 1
    k_scale : int, optional
        Frequency scaling (typically 1, 2 in case of SHG), by default 1
    f0_scale : int, optional
        Frequency scaling of f0 (typically 1, 2 for measurements with visible branch), by default 1
    f_offset : float, optional
        Offset frequency in Hz from the counted beatnote, by default 0.0

    Returns
    -------
    ndarray
        Fractional frequency y
    """
    # ensure type where appropriate
    df_nom = decimal.Decimal(nominal.strip("'"))
    N = int(N)
    df_rep = decimal.Decimal(f_rep)
    df0 = decimal.Decimal(f0) * decimal.Decimal(f0_scale)
    f_beat_sign = int(f_beat_sign)
    k_scale = int(k_scale)
    df_offset = decimal.Decimal(f_offset)

    f_nom = float(df_nom)

    f_beat = np.abs(f_beat * k_scale) * f_beat_sign

    # fN = N*f_rep + f0
    # fabs = k*(fN + f_beat) + f_offset
    # delta = fabs - f_nom
    # =>
    # delta = k*(fN + f_beat) + f_offset -f_nom = k*f_beat + f_cor
    # f_cor = k*fN + f_offset -f_nom

    f_cor = float(k_scale * (df_rep * N + df0) + df_offset - df_nom)

    # minus sign to give HM/DO
    y = -(f_beat + f_cor) / f_nom

    return y
