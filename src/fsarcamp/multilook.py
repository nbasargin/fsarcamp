"""
Functions to convert between window size in pixels and meters,
and get the effective number of looks.
"""


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
    px_spacing_az, px_spacing_rg = float(rdp_params["ps_az"]), float(rdp_params["ps_rg"])  # Pixel spacing
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
    px_spacing_az, px_spacing_rg = float(rdp_params["ps_az"]), float(rdp_params["ps_rg"])  # Pixel spacing
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
    resolution_az, resolution_rg = float(rdp_params["res_az"]), float(rdp_params["res_rg"])  # Processed resolution
    # miltilooked resolution
    ml_meters_az, ml_meters_rg = convert_pixels_to_meters(rdp_params, pixels_az, pixels_rg)
    # Effective number of looks
    looks_az = max(ml_meters_az / resolution_az, 1)
    looks_rg = max(ml_meters_rg / resolution_rg, 1)
    return looks_az, looks_rg


def convert_looks_to_pixels(rdp_params, looks_az, looks_rg):
    """
    Compute the window size in pixels to get the effective number of looks.
    Parameters:
        rdp_params is a dictionary (coming from F-SAR metadata XML file) with the following keys:
            "ps_az", "ps_rg" - Pixel spacing in azimuth and range
            "res_az", "res_rg" - Processed resolution in azimuth and range
        looks_az, looks_rg - number of looks in azimuth and range to be obtained
    Returns
        pixels_az, pixels_rg - window size in pixels to approximately get the specified number of looks
    """
    resolution_az, resolution_rg = float(rdp_params["res_az"]), float(rdp_params["res_rg"])  # Processed resolution
    # window size in meters to get the specified number of looks
    meters_az = resolution_az * looks_az
    meters_rg = resolution_rg * looks_rg
    return convert_meters_to_pixels(rdp_params, meters_az, meters_rg)
