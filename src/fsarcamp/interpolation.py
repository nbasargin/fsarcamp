import numpy as np
from matplotlib.tri import Triangulation, LinearTriInterpolator
import warnings
from .slantrange2geo import SlantRange2Geo


def _great_circle_distance(lon1, lat1, lon2, lat2):
    """Approximate distance between points"""
    r = 6371000  # Approximate radius of Earth in m
    dlon = np.radians(lon2) - np.radians(lon1)
    dlat = np.radians(lat2) - np.radians(lat1)
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.atan2(np.sqrt(a), np.sqrt(1 - a))
    distance = r * c
    return distance


def _get_longest_edge(p1, p2, p3):
    lon1, lat1 = p1
    lon2, lat2 = p2
    lon3, lat3 = p3
    d12 = _great_circle_distance(lon1, lat1, lon2, lat2)
    d23 = _great_circle_distance(lon2, lat2, lon3, lat3)
    d31 = _great_circle_distance(lon3, lat3, lon1, lat1)
    return max(d12, d23, d31)


def interpolate_points_longlat_to_lut(
    longitude,
    latitude,
    point_values,
    lut: SlantRange2Geo,
    max_triangle_edge_meters=np.inf,
):
    """
    Linearly interpolate data values assigned to points in longitude-latitude coordinates.
    The output grid covers the same area as the provided F-SAR geocoding lookup table (LUT).
    The longitude-latitude coordinates are converted to the CRS of the provided LUT.

    The algorithm internally triangulates the space in the LUT CRS coordinates.
    To filter out large triangles in areas where data points are sparse,
    restrict the maximal edge length with max_triangle_edge_meters.
    Triangle edge lengths are computed from longitude-latitude great circle distances and are approximate.
    """
    if len(point_values) < 3:
        warnings.warn("Not enough points to interpolate!")
        return np.full(lut.lut_az.shape, fill_value=np.nan)
    max_row, max_col = lut.lut_az.shape
    xs, ys = lut.geocode_coords_longlat_to_crs(longitude, latitude)
    rows, cols = lut.geocode_coords_crs_to_rowcol(xs, ys)
    triangulation_lut = Triangulation(rows, cols)  # triangulation
    # compute edge lengths, keep small triangles
    triangles = triangulation_lut.triangles
    coords_longlat = np.stack((longitude, latitude), axis=1)
    triangle_points = [coords_longlat[tri] for tri in triangles]
    longest_edges = np.array([_get_longest_edge(p1, p2, p3) for p1, p2, p3 in triangle_points])
    triangulation_lut.set_mask(longest_edges > max_triangle_edge_meters)
    # interpolate to the LUT grid
    interpolator = LinearTriInterpolator(triangulation_lut, point_values)
    axis_lut_row, axis_lut_col = np.arange(max_row), np.arange(max_col)
    grid_lut_row, grid_lut_col = np.meshgrid(axis_lut_row, axis_lut_col, indexing="ij")
    interpolated_data_lut = interpolator(grid_lut_row, grid_lut_col)
    return interpolated_data_lut.filled(np.nan)


def interpolate_points_longlat_to_slc(
    longitude,
    latitude,
    point_values,
    lut: SlantRange2Geo,
    slc_shape,
    max_triangle_edge_meters=np.inf,
):
    """
    Linearly interpolate data values assigned to points in longitude-latitude coordinates.
    The output grid covers the same area as the F-SAR SLC image (radar coordinates).
    The radar coordinates run along the azimuth (az) and range (rg) axes.

    The algorithm internally triangulates the space in the azimuth-range coordinates.
    To filter out large triangles in areas where data points are sparse,
    restrict the maximal edge length with max_triangle_edge_meters.
    Triangle edge lengths are computed from longitude-latitude great circle distances and are approximate.
    """
    if len(point_values) < 3:
        warnings.warn("Not enough points to interpolate!")
        return np.full(slc_shape, fill_value=np.nan)
    max_az, max_rg = slc_shape
    az, rg = lut.geocode_coords_longlat_to_azrg(longitude, latitude)
    triangulation_lut = Triangulation(az, rg)  # triangulation
    # compute edge lengths, keep small triangles
    triangles = triangulation_lut.triangles
    coords_longlat = np.stack((longitude, latitude), axis=1)
    triangle_points = [coords_longlat[tri] for tri in triangles]
    longest_edges = np.array([_get_longest_edge(p1, p2, p3) for p1, p2, p3 in triangle_points])
    triangulation_lut.set_mask(longest_edges > max_triangle_edge_meters)
    # interpolate to the SLC grid
    interpolator = LinearTriInterpolator(triangulation_lut, point_values)
    axis_az, axis_rg = np.arange(max_az), np.arange(max_rg)
    grid_az, grid_rg = np.meshgrid(axis_az, axis_rg, indexing="ij")
    interpolated_data_slc = interpolator(grid_az, grid_rg)
    return interpolated_data_slc.filled(np.nan)
