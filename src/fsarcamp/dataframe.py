import shapely
import pandas as pd
import geopandas as gpd


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
