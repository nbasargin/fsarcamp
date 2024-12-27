"""
Functions to convert PolSAR data to Pauli RGB images.
"""

import numpy as np
from scipy.ndimage import uniform_filter


def _clip_pauli_rgb(pauli_r, pauli_g, pauli_b, rgb_vmax=None):
    """
    Transform each color channel from the [0, color_max] to the [0, 1] range, by clipping to the max color values defined in rgb_vmax.
    If rgb_vmax is not provided, the max values will be computed from the current image as mean(color_channel) * 2.
    """
    if rgb_vmax is None:
        rgb_vmax = np.nanmean(pauli_r) * 2, np.nanmean(pauli_g) * 2, np.nanmean(pauli_b) * 2
    pauli_r_n = np.clip(pauli_r / rgb_vmax[0], a_min=0, a_max=1)
    pauli_g_n = np.clip(pauli_g / rgb_vmax[1], a_min=0, a_max=1)
    pauli_b_n = np.clip(pauli_b / rgb_vmax[2], a_min=0, a_max=1)
    return pauli_r_n, pauli_g_n, pauli_b_n


def slc_to_pauli_rgb(slc_hh, slc_hv, slc_vh, slc_vv, window_az, window_rg, rgb_vmax=None):
    """
    Transform SLCs into Pauli RGB channels.
    Parameters:
        slc_hh, slc_hv, slc_vh, slc_vv - numpy array with SLC data, same shape
        window_az, window_rg - multilook window in pixels for azimuth and range
        rgb_vmax - optional color max values, clipping is performed according to clip_pauli_rgb(r, g, b, rgb_vmax)
    Returns:
        r, g, b - Pauli RGB values, same shape as the SLCs, float values from 0 to 1
    Usage:
        r, g, b = slc_to_pauli_rgb(hh, hv, vh, vv, window_az=5, window_rg=5, rgb_vmax=(red_max, green_max, blue_max))
    To plot a 2D image with matplotlib, stack the channels along the last axis:
        rgb = np.stack((r, g, b), axis=2)
        ax.imshow(rgb)
    """
    pauli_r = uniform_filter(np.abs(slc_hh - slc_vv), (window_az, window_rg), mode="constant", cval=0)
    pauli_g = uniform_filter(np.abs(slc_hv + slc_vh), (window_az, window_rg), mode="constant", cval=0)
    pauli_b = uniform_filter(np.abs(slc_hh + slc_vv), (window_az, window_rg), mode="constant", cval=0)
    return _clip_pauli_rgb(pauli_r, pauli_g, pauli_b, rgb_vmax)


def coherency_matrix_to_pauli_rgb(t3, rgb_vmax=None):
    """
    Transform coherency matrix T entries into Pauli RGB channels.
    Parameters:
        t3 - numpy array with coherency matrices, shape (*B, 3, 3) where B are the batch dimensions
        rgb_vmax - optional color max values, clipping is performed according to clip_pauli_rgb(r, g, b, rgb_vmax)
    Returns:
        r, g, b - Pauli RGB values, shape (*B,), float values from 0 to 1
    Usage:
        r, g, b = to_pauli_rgb(t3, rgb_vmax=(red_max, green_max, blue_max))
    To plot a 2D image with matplotlib, stack the channels along the last axis:
        rgb = np.stack((r, g, b), axis=2)
        ax.imshow(rgb)
    """
    hh_plus_vv_squared = 2 * np.abs(t3[..., 0, 0])
    hh_minus_vv_squared = 2 * np.abs(t3[..., 1, 1])
    two_hv_squared = 2 * np.abs(t3[..., 2, 2])
    pauli_r = np.sqrt(hh_minus_vv_squared)
    pauli_g = np.sqrt(two_hv_squared)
    pauli_b = np.sqrt(hh_plus_vv_squared)
    return _clip_pauli_rgb(pauli_r, pauli_g, pauli_b, rgb_vmax)
