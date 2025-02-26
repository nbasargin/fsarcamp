import shapely
import fsarcamp as fc


class GeocodedRegions:
    """
    Collection of geometry in longitude-latitude coordinates.
    The geometry that can be geocoded to the GTC lookup table (LUT) or SLC coordinates.
    """

    def __init__(self):
        self._geometry_longlat_dict = dict()

    def set_geometry_longlat(self, geometry_name: str, geometry_longlat: shapely.Geometry):
        self._geometry_longlat_dict[geometry_name] = geometry_longlat

    def get_geometry_longlat(self, geometry_name: str) -> shapely.Geometry:
        """Get region geometry (e.g., polygon) in longitude-latitude coordinates."""
        return self._geometry_longlat_dict[geometry_name]

    def get_geometry_lutindices(self, geometry_name: str, lut: fc.Geo2SlantRange) -> shapely.Geometry:
        """Get region geometry (e.g., polygon) where each vertex represents indices of the F-SAR GTC LUT."""
        geo_longlat = self.get_geometry_longlat(geometry_name)
        geo_eastnorth = fc.geocode_geometry_longlat_to_eastnorth(geo_longlat, lut.projection)
        geo_lutindices = fc.geocode_geometry_eastnorth_to_lutindices(geo_eastnorth, lut)
        return geo_lutindices

    def get_geometry_azrg(self, geometry_name: str, lut: fc.Geo2SlantRange) -> shapely.Geometry:
        """Get region geometry (e.g., polygon) in azimuth-range coordinates of a specific F-SAR pass, based on LUT."""
        geo_longlat = self.get_geometry_longlat(geometry_name)
        return fc.geocode_geometry_longlat_to_azrg(geo_longlat, lut)

    def get_geometry_names(self) -> list[str]:
        return list(self._geometry_longlat_dict.keys())
