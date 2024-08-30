import decimal

import numpy as np


def beat2y(
    f_beat, nominal, N, f_rep, f0, f_beat_sign=1, k_scale=1, f0_scale=1, f_offset=0.0
):
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
