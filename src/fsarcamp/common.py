"""
Common functions, helpers, and utilities.
"""

import numpy as np
from scipy.ndimage import uniform_filter


def complex_coherence(img_1, img_2, window_size):
    """
    Estimate the complex coherence of two complex images.
    Window size can either be a single number or a tuple with two numbers.
    """
    multilook = lambda img: uniform_filter(img, window_size, mode="constant", cval=0)
    abs_squared = lambda img: img.real**2 + img.imag**2  # equivalent to np.abs(img) ** 2
    interferogram = multilook(img_1 * np.conj(img_2))
    abs_sqr_img_1 = multilook(abs_squared(img_1))
    abs_sqr_img_2 = multilook(abs_squared(img_2))
    return interferogram / np.sqrt(abs_sqr_img_1 * abs_sqr_img_2)
