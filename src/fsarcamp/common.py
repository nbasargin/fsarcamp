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
    abs_squared = lambda img: img.real ** 2 + img.imag ** 2 # equivalent to np.abs(img) ** 2
    interferogram = multilook(img_1 * np.conj(img_2))
    abs_sqr_img_1 = multilook(abs_squared(img_1))
    abs_sqr_img_2 = multilook(abs_squared(img_2))
    return interferogram / np.sqrt(abs_sqr_img_1 * abs_sqr_img_2)

# Spatial resolution, multi-look size, etc.

def convert_meters_to_pixels(rdp_params, meters_az, meters_rg):
    """
    Compute window size in pixels, given the goal resolution in meters.
    Parameters:
        rdp_params is a dictionary (coming from F-SAR metadata XML file) with the following keys:
            "ps_az", "ps_rg" - Pixel spacing in azimuth and range
            "res_az", "res_rg" - Processed resolution in azimuth and range
        meters_az, meters_rg - goal resolution of the window in meters, in azimuth and range
    Returns:
        pixels_az, pixels_rg - window size in pixels to approximately get the specified size in meters
    """
    px_spacing_az, px_spacing_rg = float(rdp_params["ps_az"]), float(rdp_params["ps_rg"]) # Pixel spacing
    pixels_az = max(round(meters_az / px_spacing_az), 1)
    pixels_rg = max(round(meters_rg / px_spacing_rg), 1)
    return pixels_az, pixels_rg

def convert_pixels_to_meters(rdp_params, pixels_az, pixels_rg):
    """
    Compute window size in meters, given the number of pixels.
    Parameters:
        rdp_params is a dictionary (coming from F-SAR metadata XML file) with the following keys:
            "ps_az", "ps_rg" - Pixel spacing in azimuth and range
            "res_az", "res_rg" - Processed resolution in azimuth and range
        pixels_az, pixels_rg - window size in pixels, in azimuth and range
    Returns:
        meters_az, meters_rg - window size in meters
    """
    px_spacing_az, px_spacing_rg = float(rdp_params["ps_az"]), float(rdp_params["ps_rg"]) # Pixel spacing
    meters_az = pixels_az * px_spacing_az
    meters_rg = pixels_rg * px_spacing_rg
    return meters_az, meters_rg

def convert_pixels_to_looks(rdp_params, pixels_az, pixels_rg):
    """
    Compute effective number of looks, given the multilook window size in pixels.
    Parameters:
        rdp_params is a dictionary (coming from F-SAR metadata XML file) with the following keys:
            "ps_az", "ps_rg" - Pixel spacing in azimuth and range
            "res_az", "res_rg" - Processed resolution in azimuth and range
        pixels_az, pixels_rg - window size in pixels, in azimuth and range
    Returns:
        looks_az, looks_rg - equivalent number of looks in azimuth and range (at least 1)
    """
    resolution_az, resolution_rg = float(rdp_params["res_az"]), float(rdp_params["res_rg"]) # Processed resolution
    # miltilooked resolution
    ml_meters_az, ml_meters_rg = convert_pixels_to_meters(rdp_params, pixels_az, pixels_rg)
    # Effective number of looks
    looks_az = max(ml_meters_az / resolution_az, 1)
    looks_rg = max(ml_meters_rg / resolution_rg, 1)
    return looks_az, looks_rg
