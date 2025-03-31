import numpy as np
from scipy.ndimage import median_filter, minimum_filter1d


def prepare_bounds(bounds, n):
    """Resize bounds to match arrays dimensions."""
    lb, ub = [np.asarray(b, dtype=float) for b in bounds]
    if lb.ndim == 0:
        lb = np.resize(lb, n)

    if ub.ndim == 0:
        ub = np.resize(ub, n)

    return lb, ub


def deglitch_from_bounds(data, bounds=(-np.inf, np.inf)):
    """Return a mask of data invalid because out of bounds.

    Parameters
    ----------
    data : array_like
        Input data
    bounds : 2-tuple of array-like, optional
        Lower and upper bounds for each column of the input array, by default (-np.inf, np.inf)

    Returns
    -------
    mask1 : array
        Mask data out of bounds.

    """
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
    """Return a mask of data from double counting. Uses numpy ptp (peak-to-peak) function.

    Parameters
    ----------
    data : array_like
        Input data_
    threshold : float, optional
        double counting threshold, by default 0.2
    glitch_ext : int, optional
        Extend glitch to neighbourg points, by default 3

    Returns
    -------
    mask2 : array
        Mask data for glitches detected by double counting.
    """
    # mask2 implement double counting
    # using numpy peak-to-peak function
    # note that this handles nicely both single counting (= no glitch detection)
    # and both an hypothetical triple counting, etc..
    ptp = np.ptp(data, axis=-1)
    mask2 = ptp < threshold
    # deglitch extend to neighbourg datapoints
    mask2 = minimum_filter1d(mask2, glitch_ext)
    return mask2


def deglitch_from_f0(f0, f0_nominal, threshold=0.25):
    """Return a mask for invalid data because f0 is out of bounds.

    Parameters
    ----------
    f0 : array_like, 1d
        array of f0 values in Hz
    f0_nominal : float or Decimal
        nominal f0 value in Hz
    threshold : float, optional
        Threshold value in Hz, by default 0.25

    Returns
    -------
    mask3 : array
        mask data for f0 out of bounds.
    """
    # mask4
    # f0
    f0_diff = f0 - np.abs(float(f0_nominal))
    mask3 = np.abs(f0_diff) < threshold

    return mask3


def deglitch_from_median_filter(f_beat, premask, median_window=60, median_threshold=250.0, glitch_ext=3):
    """Return a mask for data dissimila to neighbors.

    Parameters
    ----------
    f_beat : array_like
        Input data
    premask : array_like
        Mask to apply to input data (from other deglitch functions)
    median_window : int, optional
        Number of point over calculating rolling median filter, by default 60
    median_threshold : float, optional
        Threshold value in Hz, by default 250.
    glitch_ext : int, optional
        Extend glitch to neighbourg points, by default 3

    Returns
    -------
    _type_
        _description_
    """
    premask = premask.astype(bool)

    if f_beat[premask].size == 0:
        return np.ones_like(premask, dtype=bool)

    rolled = median_filter(f_beat[premask], median_window)
    mask4 = (
        abs(f_beat[premask] - rolled) < median_threshold
    )  # 250 Hz correspond to a 5 sigma criteria assuming 1e-13 at 1 s
    mask4 = minimum_filter1d(mask4, glitch_ext)

    if mask4.shape != f_beat[premask].shape:
        raise ValueError(f"Shape mismatch: mask4={mask4.shape}, f_beat[premask]={f_beat[premask].shape}")

    # mask3 applies oly to already masked data
    emask4 = np.ones_like(premask).astype(bool)
    emask4[premask] = mask4

    return emask4
