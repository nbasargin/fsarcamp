"""
Data loaders for F-SAR campaigns, including:
- F-SAR radar data (e.g. SLC, incidence)
- geocoding lookup tables (LUT)
- campaign ground measurements (if available)
"""

# Re-exporting internal functionality
from .common import complex_coherence
from .ste_io.ste_io import rrat, mrrat, RatFile
from .multilook import (
    convert_meters_to_pixels,
    convert_pixels_to_meters,
    convert_pixels_to_looks,
    convert_looks_to_pixels,
)
from .fs_utils import get_polinsar_folder
from .fsar_lut import Geo2SlantRange
from .fsar_lut_crop import GeoCrop
from .fsar_parameters import get_fsar_center_frequency, get_fsar_wavelength
from .pauli_rgb import slc_to_pauli_rgb, coherency_matrix_to_pauli_rgb
from .polsar import slc_to_coherency_matrix, h_a_alpha_decomposition
from .geocoding import nearest_neighbor_lookup
from .geocoding import geocode_coords_longlat_to_eastnorth, geocode_coords_eastnorth_to_lutindices
from .geocoding import geocode_coords_lutindices_to_azrg, geocode_coords_longlat_to_azrg
from .geocoding import geocode_geometry_longlat_to_eastnorth, geocode_geometry_eastnorth_to_lutindices
from .geocoding import geocode_geometry_lutindices_to_azrg, geocode_geometry_longlat_to_azrg
from .geocoding import geocode_dataframe_longlat
from .geocoding import filter_dataframe_longlat_by_geometry, filter_dataframe_longlat_by_geometry_list
from .geocoded_regions import GeocodedRegions
from .interpolation import interpolate_points_longlat_to_lut_region, interpolate_points_longlat_to_slc_region
