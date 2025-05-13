import numpy as np
from matplotlib.tri import Triangulation, LinearTriInterpolator
import warnings
import fsarcamp as fc


def _get_longest_edge(p1, p2, p3):
    d12 = np.linalg.norm(p1 - p2)
    d23 = np.linalg.norm(p2 - p3)
    d31 = np.linalg.norm(p3 - p1)
    return max(d12, d23, d31)


def interpolate_points_longlat_to_lut_region(
    longitude,
    latitude,
    point_values,
    lut: fc.Geo2SlantRange,
    lut_n_min,
    lut_n_max,
    lut_e_min,
    lut_e_max,
    max_triangle_edge_meters=np.inf,
):
    """
    Linearly interpolate data values assigned to points in longitude-latitude coordinates.
    The output grid covers a region of the F-SAR geocoding lookup table (LUT).
    The region extent is specified by (lut_n_min, lut_n_max, lut_e_min, lut_e_max).
    The coordinates are the LUT indices along the northing (n) and easting (e) axes.

    The algorithm internally triangulates the space according to the data coordinates.
    To filter out large triangles in areas where data points are sparse,
    restrict the maximal edge length with max_triangle_edge_meters.
    """
    if len(point_values) < 3:
        warnings.warn("Not enough points to interpolate!")
        shape = (lut_n_max - lut_n_min, lut_e_max - lut_e_min)
        return np.full(shape, fill_value=np.nan)
    # geocode longlat to eastnorth and lutindices
    easting, northing = fc.geocode_coords_longlat_to_eastnorth(longitude, latitude, lut.projection)
    lut_n, lut_e = fc.geocode_coords_eastnorth_to_lutindices(easting, northing, lut)
    # triangulation in LUT indices
    triangulation_lut = Triangulation(lut_n, lut_e)
    # compute edge lengths in eastnorth, keep small triangles
    triangles = triangulation_lut.triangles
    coords_eastnorth = np.stack((easting, northing), axis=1)
    triangle_points = [coords_eastnorth[tri] for tri in triangles]
    longest_edges = np.array([_get_longest_edge(p1, p2, p3) for p1, p2, p3 in triangle_points])
    triangulation_lut.set_mask(longest_edges > max_triangle_edge_meters)
    # interpolate to the LUT region
    interpolator = LinearTriInterpolator(triangulation_lut, point_values)
    axis_lut_n, axis_lut_e = np.arange(lut_n_min, lut_n_max), np.arange(lut_e_min, lut_e_max)
    grid_lut_n, grid_lut_e = np.meshgrid(axis_lut_n, axis_lut_e, indexing="ij")
    interpolated_data_lutregion = interpolator(grid_lut_n, grid_lut_e)
    return interpolated_data_lutregion.filled(np.nan)


def interpolate_points_longlat_to_slc_region(
    longitude,
    latitude,
    point_values,
    lut: fc.Geo2SlantRange,
    az_min,
    az_max,
    rg_min,
    rg_max,
    max_triangle_edge_meters=np.inf,
):
    """
    Linearly interpolate data values assigned to points in longitude-latitude coordinates.
    The output grid covers a region of the F-SAR SLC image (radar coordinates).
    The region extent is specified by (az_min, az_max, rg_min, rg_max).
    The radar coordinates run along the azimuth (az) and range (rg) axes.

    The algorithm internally triangulates the space according to the data coordinates.
    To filter out large triangles in areas where data points are sparse,
    restrict the maximal edge length with max_triangle_edge_meters.
    """
    if len(point_values) < 3:
        warnings.warn("Not enough points to interpolate!")
        shape = (az_max - az_min, rg_max - rg_min)
        return np.full(shape, fill_value=np.nan)
    # geocode longlat to eastnorth and lutindices
    easting, northing = fc.geocode_coords_longlat_to_eastnorth(longitude, latitude, lut.projection)
    lut_n, lut_e = fc.geocode_coords_eastnorth_to_lutindices(easting, northing, lut)
    az, rg = fc.geocode_coords_lutindices_to_azrg(lut_n, lut_e, lut)
    # triangulation in LUT indices
    triangulation_lut = Triangulation(az, rg)
    # compute edge lengths in eastnorth, keep small triangles
    triangles = triangulation_lut.triangles
    coords_eastnorth = np.stack((easting, northing), axis=1)
    triangle_points = [coords_eastnorth[tri] for tri in triangles]
    longest_edges = np.array([_get_longest_edge(p1, p2, p3) for p1, p2, p3 in triangle_points])
    triangulation_lut.set_mask(longest_edges > max_triangle_edge_meters)
    # interpolate to the LUT region
    interpolator = LinearTriInterpolator(triangulation_lut, point_values)
    axis_az, axis_rg = np.arange(az_min, az_max), np.arange(rg_min, rg_max)
    grid_az, grid_rg = np.meshgrid(axis_az, axis_rg, indexing="ij")
    interpolated_data_slcregion = interpolator(grid_az, grid_rg)
    return interpolated_data_slcregion.filled(np.nan)
