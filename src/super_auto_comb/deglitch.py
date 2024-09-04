import numpy as np
from scipy.ndimage import median_filter, minimum_filter1d


def prepare_bounds(bounds, n):
    lb, ub = [np.asarray(b, dtype=float) for b in bounds]
    if lb.ndim == 0:
        lb = np.resize(lb, n)

    if ub.ndim == 0:
        ub = np.resize(ub, n)

    return lb, ub


def deglitch_from_bounds(data, bounds=(-np.inf, np.inf)):
    # from scipy curve_fit
    # bounds 2-tuple of array_like: Each element of the tuple must be either an array with the length equal to the number of parameters, or a scalar
    data = np.atleast_2d(data)
    N = data.shape[1]
    if len(bounds) == 2:
        lb, ub = prepare_bounds(bounds, N)
    else:
        raise ValueError("`bounds` must contain 2 elements.")

    if lb.shape != (N,) or ub.shape != (N,):
        raise ValueError("Inconsistent shapes between bounds and columns.")

    if np.any(lb >= ub):
        raise ValueError("Each lower bound must be strictly less than each upper bound.")

    # mask1 is all data in filter range
    mask1 = (data > lb).all(axis=-1) & (data < ub).all(axis=-1)
    return mask1


def deglitch_from_double_counting(data, threshold=0.2, glitch_ext=3):
    # mask2 implement double counting
    # using numpy peak-to-peak function
    # note that this handles nicely both single counting (= no glitch detection)
    # and both an hypothetical triple counting, etc..
    ptp = np.ptp(data, axis=-1)
    mask2 = ptp < threshold
    # deglitch extend to neighbourg datapoints
    mask2 = minimum_filter1d(mask2, glitch_ext)
    return mask2


def deglitch_from_median_filter(f_beat, premask, median_window=60, median_threshold=250, glitch_ext=3):
    rolled = median_filter(f_beat[premask], median_window)
    mask3 = (
        abs(f_beat[premask] - rolled) < median_threshold
    )  # 250 Hz correspond to a 5 sigma criteria assuming 1e-13 at 1 s
    mask3 = minimum_filter1d(mask3, glitch_ext)
    # mask3 applies oly to already masked data
    emask3 = np.ones_like(premask).astype(bool)
    emask3[premask] = mask3

    return emask3


def deglitch_from_f0(f0, f0_nominal, threshold=0.25):
    # mask4
    # f0
    f0_diff = f0 - np.abs(float(f0_nominal))
    mask4 = np.abs(f0_diff) < threshold

    return mask4


# def deglitch(
#     alldata,
#     columns,
#     bounds=(-np.inf, np.inf),
#     los=0.0,
#     threshold=0.2,
#     glitch_ext=3,
#     median_window=60,
#     median_threshold=250.0,
# ):
#     """Deglitch comb data along given columns.
#     1. Each column is compared by some bounds and shifted by a local oscillator.
#     2. Glitches are detected as differences between the columns exceeding a threshold.
#     3. A median filter is applied to reduce junk data

#     Parameters
#     ----------
#     alldata : ndarray
#             KK data extracted by genfromkk
#     columns : int or array-like
#             columns to be deglitched
#     bounds : tuple, optional
#             2-tuple of array_like, by default (-np.inf, np.inf)
#             Each element of the tuple must be either an array with the length equal to the number of columns, or a scalar
#     los : float or array-like, optional
#             Local oscillators to be added to each column, by default 0.
#     threshold : float, optional
#             Deglitch mask threshold, by default 0.2


#     """
#     # columns could be a int or an array like
#     columns = np.atleast_1d(columns).astype(int)
#     N = columns.shape[0]

#     data = alldata[:, columns]

#     mask1 = deglitch_from_bounds(data, columns, bounds)

#     # local oscillators
#     los = np.resize(np.asarray(los, dtype=float), N)
#     data = np.abs(data + los)

#     fbeat = np.mean(data, axis=-1)

#     mask2 = deglitch_from_double_counting(data, threshold, glitch_ext)

#     # mask3 median-filter
#     mask = mask1 & mask2
#     rolled = median_filter(fbeat[mask], median_window)
#     mask3 = (
#         abs(fbeat[mask] - rolled) < median_threshold
#     )  # 250 Hz correspond to a 5 sigma criteria assuming 1e-13 at 1 s
#     mask3 = minimum_filter1d(mask3, glitch_ext)
#     # mask3 applies oly to already masked data
#     emask3 = np.ones_like(mask).astype(bool)
#     emask3[mask] = mask3

#     return fbeat, mask1, mask2, emask3, ptp
