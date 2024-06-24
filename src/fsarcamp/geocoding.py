"""
Functions related to geocoding and pixel lookup.
"""
import numpy as np
import fsarcamp as fc
import pyproj

def nearest_neighbor_lookup(img: np.ndarray, lut_az, lut_rg, inv_value=np.nan) -> np.ndarray:
    """
    Lookup pixels in the image (img) given the indices (lut_az, lut_rg).
    Nearest neighbor lookup is used which is faster but less accurate than interpolation.    
    This function can be used to geocode data from the SLC to geographic coordinates using the F-SAR lookup tables (LUT).

    Parameters:
        img: numpy array of shape (az, rg, *C) where C are the optional channels (or other dimensions)
            the first two dimensions of the image correspond to the azimuth and range, respectively
        lut_az, lut_rg: numpy arrays of shape (*L)
            lookup tables for pixel-lookup, store the indices of pixels to be looked up
            if the indices are floats, the indices are rounded to the nearest integer to get the pixel coordinates
        inv_value: constant value to fill pixels with invalid indices, optional, default: numpy.nan
    Returns:
        numpy array of shape (*L, *C), with pixel values looked up from img at indices (lut_az, lut_rg)
        pixels where the indices are invalid (e.g., outside of the img) are filled with inv_value
    Example usage:
        slc_data = ... # some data in SLC coordinates, can have multiple channels, example shape (2000, 1000, 3)
        lut_az, lut_rg = ... # F-SAR lookup tables, example shape (500, 600)
        geocoded = nearest_neighbor_lookup(slc_data, lut_az, lut_rg) # resulting shape (500, 600, 3)
    """
    # round values in lookup tables (this creates a copy of the LUT data, so inline operations are allowed later)
    lut_rg = np.rint(lut_rg)
    lut_az = np.rint(lut_az)
    # determine invalid positions
    max_az, max_rg = img.shape[0], img.shape[1]
    invalid_positions = np.isnan(lut_az) | np.isnan(lut_rg) | (lut_az < 0) | (lut_az >= max_az) | (lut_rg < 0) | (lut_rg >= max_rg)
    # set invalid positions to 0
    lut_az[invalid_positions] = 0
    lut_rg[invalid_positions] = 0
    # convert to integer indices
    lut_rg = lut_rg.astype(np.int64)
    lut_az = lut_az.astype(np.int64)
    # nearest neighbor lookup
    geocoded = img[lut_az, lut_rg]
    # apply invalid mask
    geocoded[invalid_positions] = inv_value
    return geocoded

def geocode_lat_lon_to_north_east(longitude, latitude, lut: fc.Geo2SlantRange):
    """
    Transform latitude-longitude coordinates to northing-easting coordinates matching the F-SAR GTC lookup table projection.
    Note: the northing-easting values are geographical coordinates and not the lookup table indices.
    """
    proj_latlong = pyproj.Proj(proj="latlong", ellps="WGS84", datum="WGS84")
    latlong_to_lut = pyproj.Transformer.from_proj(proj_latlong, lut.projection)
    easting, northing = latlong_to_lut.transform(longitude, latitude)
    return northing, easting

def geocode_north_east_to_az_rg(northing, easting, lut: fc.Geo2SlantRange):
    """
    Geocode northing-easting coordinates (projection of the F-SAR GTC lookup table) to SLC geometry (azimuth-range).
    First, the appropriate pixels corresponding to the northing-easting coordinates are selected in the lookup table.
    The lookup table then provides the azimuth and range indices at the pixel positions.
    """
    lut_northing_idx = np.rint((northing - lut.min_north) / lut.pixel_spacing_north).astype(np.int64)
    lut_easting_idx = np.rint((easting - lut.min_east) / lut.pixel_spacing_east).astype(np.int64)
    azimuth_idx = lut.lut_az[lut_northing_idx, lut_easting_idx]
    range_idx = lut.lut_rg[lut_northing_idx, lut_easting_idx]
    return azimuth_idx, range_idx

def geocode_lat_lon_to_az_rg(longitude, latitude, lut: fc.Geo2SlantRange):
    """
    Geocode latitude-longitude coordinates to SLC geometry (azimuth-range) using the F-SAR GTC lookup table.
    This function applies `geocode_lat_lon_to_north_east` followed by `geocode_north_east_to_az_rg`.
    """
    northing, easting = geocode_lat_lon_to_north_east(longitude, latitude, lut)
    azimuth_idx, range_idx = geocode_north_east_to_az_rg(northing, easting, lut)
    return azimuth_idx, range_idx
