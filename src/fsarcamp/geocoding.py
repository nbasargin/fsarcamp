"""
Functions related to geocoding and pixel lookup.
"""

import numpy as np
import fsarcamp as fc
import pyproj
import shapely
import shapely.ops as ops
import pandas as pd
import geopandas as gpd


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
    invalid_positions = (
        np.isnan(lut_az) | np.isnan(lut_rg) | (lut_az < 0) | (lut_az >= max_az) | (lut_rg < 0) | (lut_rg >= max_rg)
    )
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


# geocoding coordinate arrays


def geocode_coords_longlat_to_eastnorth(longitude, latitude, lut_projection: pyproj.Proj):
    """
    Transform longitude-latitude coordinates to coordinates matching the F-SAR GTC lookup table projection.
    Note: the easting-northing values are geographical coordinates (and not the lookup table indices).
    """
    proj_longlat = pyproj.Proj(proj="longlat", ellps="WGS84", datum="WGS84")
    longlat_to_eastnorth = pyproj.Transformer.from_proj(proj_longlat, lut_projection)
    easting, northing = longlat_to_eastnorth.transform(longitude, latitude)
    return easting, northing


def geocode_coords_eastnorth_to_lutindices(easting, northing, lut: fc.Geo2SlantRange):
    """
    Convert easting-northing coordinates (projection of the F-SAR GTC lookup table) to lookup table indices.
    There are no checks whether the points are inside the lookup table.
    The indices are rounded to integers but remain float-valued to preserve invalid NaN values.
    """
    easting = np.array(easting)
    northing = np.array(northing)
    lut_n = np.rint((northing - lut.min_north) / lut.pixel_spacing_north)
    lut_e = np.rint((easting - lut.min_east) / lut.pixel_spacing_east)
    return lut_n, lut_e


def geocode_coords_lutindices_to_azrg(lut_n, lut_e, lut: fc.Geo2SlantRange):
    """
    Geocode lookup table indices to SLC geometry (azimuth-range).
    First, the appropriate pixels are selected in the lookup table.
    The lookup table then provides the azimuth and range values (float-valued) at the pixel positions.
    The azimuth and range values are invalid and set to NaN if any of the following is true:
    - input lookup table indices are are NaN
    - input lookup table indices are outside of the lookup table
    - retrieved azimuth or range values are negative (meaning the area is not covered by the SLC)
    """
    lut_n = np.array(lut_n)
    lut_e = np.array(lut_e)
    # if some coords are NaN or outside of the lut, set them to valid values before lookup, mask out later
    max_n, max_e = lut.lut_az.shape
    invalid_idx = np.isnan(lut_n) | np.isnan(lut_e) | (lut_n < 0) | (lut_n >= max_n) | (lut_e < 0) | (lut_e >= max_e)
    if np.isscalar(invalid_idx):
        if invalid_idx:
            return np.nan, np.nan  # only a single position provided and it is invalid
    else:  # not scalar
        lut_n[invalid_idx] = 0
        lut_e[invalid_idx] = 0
    # get azimuth and range positions
    lut_n_idx = lut_n.astype(np.int64)
    lut_e_idx = lut_e.astype(np.int64)
    az = lut.lut_az[lut_n_idx, lut_e_idx]
    rg = lut.lut_rg[lut_n_idx, lut_e_idx]
    # clear invalid azimuth and range
    invalid_results = invalid_idx | (az < 0) | (rg < 0)
    if np.isscalar(invalid_results):
        if invalid_results:
            return np.nan, np.nan  # only a single position computed and it is invalid
    else:  # not scalar
        az[invalid_results] = np.nan
        rg[invalid_results] = np.nan
    return az, rg


def geocode_coords_longlat_to_azrg(longitude, latitude, lut: fc.Geo2SlantRange):
    easting, northing = geocode_coords_longlat_to_eastnorth(longitude, latitude, lut.projection)
    lut_northing, lut_easting = fc.geocode_coords_eastnorth_to_lutindices(easting, northing, lut)
    az, rg = fc.geocode_coords_lutindices_to_azrg(lut_northing, lut_easting, lut)
    return az, rg


# geocoding shapely geometry


def geocode_geometry_longlat_to_eastnorth(geometry_longlat: shapely.Geometry, lut_projection: pyproj.Proj):
    proj_longlat = pyproj.Proj(proj="longlat", ellps="WGS84", datum="WGS84")
    longlat_to_eastnorth = pyproj.Transformer.from_proj(proj_longlat, lut_projection)
    return ops.transform(longlat_to_eastnorth.transform, geometry_longlat)


def geocode_geometry_eastnorth_to_lutindices(geometry_eastnorth: shapely.Geometry, lut: fc.Geo2SlantRange):
    eastnorth_to_lutindices = lambda e, n: geocode_coords_eastnorth_to_lutindices(e, n, lut)
    try:
        return ops.transform(eastnorth_to_lutindices, geometry_eastnorth)
    except:
        return None  # invalid shapes (e.g. outside LUT or SLC) throw errors


def geocode_geometry_lutindices_to_azrg(geometry_lutindices: shapely.Geometry, lut: fc.Geo2SlantRange):
    lutindices_to_azrg = lambda lut_n, lut_e: geocode_coords_lutindices_to_azrg(lut_n, lut_e, lut)
    try:
        return ops.transform(lutindices_to_azrg, geometry_lutindices)
    except:
        return None  # invalid shapes (e.g. outside LUT or SLC) throw errors


def geocode_geometry_longlat_to_azrg(geometry_longlat: shapely.Geometry, lut: fc.Geo2SlantRange):
    shape_eastnorth = geocode_geometry_longlat_to_eastnorth(geometry_longlat, lut.projection)
    shape_lutincides = geocode_geometry_eastnorth_to_lutindices(shape_eastnorth, lut)
    shape_azrg = geocode_geometry_lutindices_to_azrg(shape_lutincides, lut)
    return shape_azrg


# pandas dataframe with longitude and latitude columns


def geocode_dataframe_longlat(df: pd.DataFrame, lut: fc.Geo2SlantRange):
    """
    Geocode a pandas dataframe with "longitude" and "latitude" columns to LUT and SLC geometry.
    Returns a new dataframe with additional columns added:
        "northing", "easting" - geographical coordinates in the LUT projection
        "lut_northing", "lut_easting" - pixel indices within the LUT
        "azimuth", "range" - pixel indices within the SLC
    """
    latitude = df["latitude"].to_numpy()
    longitude = df["longitude"].to_numpy()
    easting, northing = fc.geocode_coords_longlat_to_eastnorth(longitude, latitude, lut.projection)
    lut_northing, lut_easting = fc.geocode_coords_eastnorth_to_lutindices(easting, northing, lut)
    az, rg = fc.geocode_coords_lutindices_to_azrg(lut_northing, lut_easting, lut)
    # extend data frame
    df_geocoded = df.assign(
        northing=northing,
        easting=easting,
        lut_northing=lut_northing,
        lut_easting=lut_easting,
        azimuth=az,
        range=rg,
    )
    return df_geocoded


def filter_dataframe_longlat_by_geometry(df: pd.DataFrame, geometry_longlat: shapely.Geometry):
    """
    Filter a pandas dataframe with "longitude" and "latitude" columns by the specified geometry (e.g. polygon).
    """
    point_locations = gpd.GeoSeries(df.apply(lambda x: shapely.Point(x["longitude"], x["latitude"]), axis=1))
    result = df[point_locations.within(geometry_longlat)]
    return result


def filter_dataframe_longlat_by_geometry_list(df: pd.DataFrame, geometry_list_longlat: list[shapely.Geometry]):
    """
    Filter a pandas dataframe with "longitude" and "latitude" columns by geometry list (e.g. several polygons).
    """
    point_locations = gpd.GeoSeries(df.apply(lambda x: shapely.Point(x["longitude"], x["latitude"]), axis=1))
    filtered_dfs = [df[point_locations.within(geom)] for geom in geometry_list_longlat]
    filtered_df = pd.concat(filtered_dfs, ignore_index=True)
    return filtered_df
