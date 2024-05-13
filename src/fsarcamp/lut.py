"""
Copy of lut.py from https://gitlab.dlr.de/hr-rko-ir-pol-insar/common_code
"""

import numpy as np
import logging
from scipy.ndimage import zoom
from scipy.interpolate import griddata, RectBivariateSpline
import pyproj

from fsarcamp.rat_io import RatFile
#from blocks_griddata import blocks_griddata_2d     # Imported later if needed


class LUT(object):
    """
    Class to represent the Look Up Table (LUT) information of an image for
    geocoding.
    """
    def __init__(self, limits, lut_rg, lut_az, proj_params=None):
        """
        Constructs the LUT with the given parameters.
        See also the from_*(...) class methods for LUT generation.

        Parameters
        ----------

        limits: array
            The limits (coordinates) of the LUT in the given projection.
            If 2 dimensions x1 and x2 are available, it should be:
            [min_x1, max_x1, min_x2, max_x2]

            NOTE: min and max corresponds to the *covered* coordinates value.
            This means that the min and max values corresponds to first and
            last pixels coordinates of the lut_rg and lut_az.
        lut_rg: array
            The range LUT array
        lut_az: array
            The azimuth LUT array
        proj_params: dict
            The parameters that define the coordinates projection
            system according to pyproj.Proj library.
            If not specified, latitude & longitude coordinates over an WGS84
            ellipsoid are assumed
            (proj='latlong', ellps='WGS84', datum='WGS84').
        """
        assert(lut_rg.shape == lut_az.shape)
        assert(len(limits) == 4)
        self.min_x1 = limits[0]
        self.max_x1 = limits[1]
        self.min_x2 = limits[2]
        self.max_x2 = limits[3]
        self.c1 = np.array([limits[0], limits[2]])
        self.c2 = np.array([limits[1], limits[3]])
        shape = lut_rg.shape
        self.x1_step = (self.max_x1-self.min_x1) / (shape[0]-1)
        self.x2_step = (self.max_x2-self.min_x2) / (shape[1]-1)
        self.lut_rg = lut_rg
        self.lut_az = lut_az
        self.proj_params=proj_params
        self.logger = logging.getLogger('LUT')
        if proj_params==None:
            # Default projection (lat/lon)
            self.proj = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
        else:
            self.proj = pyproj.Proj(**proj_params)

    def get_Proj(self):
        """
        Returns the pyproj.Proj projection
        """
        return self.proj

    def get_extent(self):
        """
        Obtains the extent of the covered area coordinates, that is, the
        minimum and maximum value for each of the coordinates.

        This is especially useful for plotting geocoded images:
            ```
            plt.imshow(geo_img, origin='lower', extent=lut.get_extent())
            ```

        Returns
        -------
        extend: ndarray, shape (4)

        """
        return np.array([self.min_x2, self.max_x2, self.min_x1, self.max_x1])

    def to_npz_file(self, fname):
        """
        Save to a compressed .npz file.

        Parameters
        ----------
        fname: string
            Filename of the output file to write the LUT.
        """
        # Old format
#        np.savez_compressed(fname, lut_rg=self.lut_rg, lut_az=self.lut_az,
#                        min_lat=self.min_lat, max_lat=self.max_lat,
#                        min_lon=self.min_lon, max_lon=self.max_lon)
        # New format
        np.savez_compressed(fname, lut_rg=self.lut_rg, lut_az=self.lut_az,
                        corners=np.array([self.c1, self.c2]),
                        proj_params=self.proj_params)

    @classmethod
    def from_lat_lon(cls, lat, lon, shape = (2500,2500), max_dim = 2500):
        """
        Loads the LUT from a set of latitude and longitude images

        Parameters
        ----------
        lat: array
            The latitude image.
        lon: array
            The longitude image
        shape: tuple (2 values), default: (2500,2500)
            The desired shape of the LUT
        max_dim: int, default: 2500
            The maximum size for all the dimensions for the interpolation.
            If this value is too high some errors may appear due to a large
            number of points to interpolate in griddata.
        """
        logger = logging.getLogger('LUT')
        #self.lut_rg = np.zeros(shape)
        #self.lut_az = np.zeros(shape)
        min_lat = np.nanmin(lat)
        max_lat = np.nanmax(lat)
        min_lon = np.nanmin(lon)
        max_lon = np.nanmax(lon)
        lat_step = (max_lat-min_lat) / (shape[0] - 1)
        lon_step = (max_lon-min_lon) / (shape[1] - 1)
        larger_dim = np.max(lat.shape)
        rlat = rlon = None
        zfactor = 1.0
        if larger_dim > max_dim:
            logger.info("The lat and lon images are larger than the maximum dimension: max({}) > {}".format(lat.shape, max_dim))
            zfactor = np.float(max_dim) / np.float(larger_dim)
            logger.info("The scale factor is {}".format(zfactor))
            rlat = zoom(lat, zfactor, order=1, mode='nearest')
            rlon = zoom(lon, zfactor, order=1, mode='nearest')
            logger.debug("Reduced size of images({})".format(rlat.shape))
        else:
            logger.info("Processing full size lat and lon images ({})".format(lat.shape))
            rlat = lat
            rlon = lon
        grid_x, grid_y = np.mgrid[0:rlat.shape[0], 0:rlat.shape[1]]
        grid_lat, grid_lon = np.mgrid[0:shape[0], 0:shape[1]]
        grid_lat = min_lat + grid_lat * lat_step
        grid_lon = min_lon + grid_lon * lon_step
        vp = np.isfinite(rlat) & np.isfinite(rlon)
        # Correction factor to reverse the shift in array positions induced by
        # the shape reduction
        f = (np.array(lat.shape, dtype=np.float) - 1.0) / (np.array(rlat.shape, dtype=np.float) - 1.0)
        lut_rg = griddata(np.transpose(np.array([rlat[vp], rlon[vp]])), grid_y[vp], (grid_lat, grid_lon)) * f[1]
        lut_az = griddata(np.transpose(np.array([rlat[vp], rlon[vp]])), grid_x[vp], (grid_lat, grid_lon)) * f[0]
        return cls([min_lat, max_lat, min_lon, max_lon], lut_rg, lut_az)

    @classmethod
    def from_npz_file(cls, fname):
        """
        Loads the LUT previously saved with lut.to_npz_file()

        Parameters
        ----------
        fname: string
            The filename of the .npz file to load the LUT.
        """
        flut = np.load(fname, allow_pickle=True)
        if np.alltrue([ label in flut.files for label in ['corners', 'proj_params', 'lut_rg', 'lut_az'] ]):
            # New format
            c1 = flut['corners'][0]
            c2 = flut['corners'][1]
            # Note: to get a dictionary from npz use [()]
            # https://stackoverflow.com/questions/22315595/saving-dictionary-of-header-information-using-numpy-savez
            return cls([c1[0], c2[0], c1[1], c2[1]], flut['lut_rg'], flut['lut_az'], flut['proj_params'][()])
        elif np.alltrue([ label in flut.files for label in ['min_lat', 'max_lat', 'min_lon', 'max_lon', 'lut_rg', 'lut_az'] ]):
            # Old format
            return cls([flut['min_lat'], flut['max_lat'], flut['min_lon'], flut['max_lon']], flut['lut_rg'], flut['lut_az'])
        else:
            raise ValueError("Invalid file. The file does not contain the required information to load the LUT object!")

    @classmethod
    def from_FSAR_lut_utm_files(cls, fname_az, fname_rg, hdr_fname=None):
        """
        Loads the LUT from FSAR utm look up tables (in RAT format).

        Parameters
        ----------
        fname_az: string
            The filename of the azimuth LUT RAT file
        fname_rg: string
            The filename of the range LUT RAT file
        hdr_fname: string, optional
            The filename of the header (.hdr) file containing the information
            of the coordinates, spacing, etc.
            If a hdr_fname is provided, the information will be readed from
            there instead of from the RAT header.
        """
        f_az = RatFile(fname_az)
        f_rg = RatFile(fname_rg)
        # Check both LUTs have same size
        assert(f_az._get_shape() == f_rg._get_shape())

        if hdr_fname == None:
            # Load params from RAT header (assuming both headers are equal)
            min_x1 = f_az.Header.Geo.min_north
            min_x2 = f_az.Header.Geo.min_east
            ps_x1 = f_az.Header.Geo.ps_north
            ps_x2 = f_az.Header.Geo.ps_east
            zone = f_az.Header.Geo.zone
            hemisphere = f_az.Header.Geo.hemisphere
            if zone < 0 and hemisphere == 2:
                # South hemisphere. Correct negative zone as it is already
                # indicated by hemisphere variable.
                zone = -zone
        else:
            # Load params from header file
            f = open(hdr_fname, 'r')
            for line in f:
                line_separate = line.split('=')
                variable = line_separate[0]
                if variable.strip() == 'min_easting':
                    min_x2 = float(line_separate[1])
                if variable.strip() == 'min_northing':
                    min_x1 = float(line_separate[1])
                if variable.strip() == 'pixel_spacing_east':
                    ps_x2 = float(line_separate[1])
                if variable.strip() == 'pixel_spacing_north':
                    ps_x1 = float(line_separate[1])
                if variable.strip() == 'projection_zone':
                    zone = int(line_separate[1])
                if variable.strip() == 'map info':
                    if line_separate[1].find('North') > 0:
                        hemisphere = 1
                    else:
                        hemisphere = 2
                # On header files it seems that 'North' is always set
                # even for southern hemisphere. The southern hemisphere
                # seems to be indicated by a negative zone value.
                if zone < 0:
                    hemisphere = 2
                    zone = -zone
            f.close()

        # Get shape from header
        shape = f_az._get_shape()
        # Calculate max coordinates
        max_x1 = min_x1 + (shape[0] - 1)*ps_x1
        max_x2 = min_x2 + (shape[1] - 1)*ps_x2
        # Generate the projection information
        proj_params = {}
        proj_params['proj'] = 'utm'
        proj_params['zone'] = zone
        # Assume WGS84 ellipsoid!
        proj_params['ellps'] = 'WGS84'
        if hemisphere == 2:
            proj_params['south'] = True
        else:
            # Assume north also if unspecified!
            proj_params['north'] = True

        return cls([min_x1, max_x1, min_x2, max_x2],
                   np.flipud(f_rg.mread()), np.flipud(f_az.mread()),
                   proj_params=proj_params)

    def resample_to_grid(self, x1_range_dest, x2_range_dest):
        """
        Resamples this LUT to the coordinate grid given by x1_range_dest and
        x2_range_dest. A new LUT object is returned.

        NOTE: The new grid should correspond to the same projection.
        """
        limits = [x1_range_dest[0], x1_range_dest[-1],
                  x2_range_dest[0], x2_range_dest[-1]]
        x1_range = self.min_x1 + np.arange(self.lut_az.shape[0]) * self.x1_step
        x2_range = self.min_x2 + np.arange(self.lut_az.shape[1]) * self.x2_step
        # Interpolate this LUT (az & rg) to lut_dest positions:

        # First make and copy...
        imgc_az = self.lut_az.copy()
        # ... and replace nans with an invalid number...
        imgc_az[~np.isfinite(imgc_az)] = -9999
        # ... as RectBivariateSpline does not accept nans.
        interp_az = RectBivariateSpline(x1_range, x2_range, imgc_az, kx=1, ky=1)
        # Now do the interpolation...
        lut_az = interp_az(x1_range_dest, x2_range_dest, grid=True)
        # ... and replace invalid values by nans again.
        lut_az[lut_az < 0] = np.nan
        imgc_az = interp_az = None  # Free some memory

        # Same procedure for rg lut
        imgc_rg = self.lut_rg.copy()
        imgc_rg[~np.isfinite(imgc_rg)] = -9999
        interp_rg = RectBivariateSpline(x1_range, x2_range, imgc_rg, kx=1, ky=1)
        lut_rg = interp_rg(x1_range_dest, x2_range_dest, grid=True)
        lut_rg[lut_rg < 0] = np.nan
        imgc_rg = interp_rg = None  # Free some memory

        # Return a new generated LUT object
        return LUT(limits, lut_rg, lut_az, proj_params=self.proj_params)

    def resample_to_other_LUT(self, lut_dest):
        """
        Resamples this LUT to the geometry of another LUT (lut_dest). A new
        LUT object is returned.

        This is useful when 2 images with two slightly different LUTs are
        compared. The LUT of salve image(s) may be resampled to the master
        one. After this, the geocoded images will be pixel by pixel
        comparable.

        NOTE: lut_dest should correspond to the same projection.
        """
        x1_rdest = lut_dest.min_x1 + np.arange(lut_dest.lut_az.shape[0]) * lut_dest.x1_step
        x2_rdest = lut_dest.min_x2 + np.arange(lut_dest.lut_az.shape[1]) * lut_dest.x2_step
        # interpolate this LUT (az & rg) to lut_dest positions
        return self.resample_to_grid(x1_rdest, x2_rdest)

    def get_axes_coordinates(self):
        """
        Returns the axes coordinates grid, according the projection of this
        LUT.

        Returns
        -------
        x1_range : array
            Coordinate values for the first dimension.
        x2_range : array
            Coordinate values for the second dimension.

        """
        x1_range = self.min_x1 + np.arange(self.lut_az.shape[0]) * self.x1_step
        x2_range = self.min_x2 + np.arange(self.lut_az.shape[1]) * self.x2_step
        return x1_range, x2_range

    def generate_RLUT(self, img_shape, method_interp='linear'):
        """
        Generates a Reverse Look-Up Table (RLUT) for fast back-geocoding based on this LUT.

        Parameters
        ----------
        img_shape: tuple
            Shape of the RLUT, typically the radar image dimensions (azimuth, range).
        method_interp: str, optional
            Interpolation method to use in numpy.griddata.
            Default is 'linear'.
        """
        # get valid points of the LUT: invalid points are negative or nans
        valid_points = np.where((self.lut_rg >= 0) & (self.lut_az >= 0) & np.isfinite(self.lut_az) & np.isfinite(self.lut_rg))
        # generate grid with azimuth / range dimensions
        max_az, max_rg = img_shape[0], img_shape[1]
        grid_az, grid_rg = np.meshgrid(np.arange(0, max_az, 1), np.arange(0, max_rg, 1), indexing='ij')
        # get lut for each coordinate
        lut_x1 = griddata(
            (self.lut_az[valid_points], self.lut_rg[valid_points]),
            valid_points[0],
            (grid_az, grid_rg),
            method=method_interp,
            rescale=True,
        )
        lut_x1 = lut_x1.astype(np.float32)
        lut_x2 = griddata(
            (self.lut_az[valid_points], self.lut_rg[valid_points]),
            valid_points[1],
            (grid_az, grid_rg),
            method=method_interp,
            rescale=True,
        )
        lut_x2 = lut_x2.astype(np.float32)
        return RLUT(lut_x1, lut_x2, self.proj, 1)


class RLUT(object):
    """
    Class to represent the Reverse Look Up Table (RLUT) information of an image
    for back-geocoding.
    """
    def __init__(self, rlut_x1, rlut_x2, proj, factor=1.0):
        """
        Constructs the RLUT with the given parameters.

        Parameters
        ----------

        rlut_x1: array
            The range RLUT array
        rlut_x2: array
            The azimuth RLUT array
        proj: pyproj.Proj
            The coordinates projection on which the RLUT returns the
            pixels coordinates.
        factor: float, optional
            Reduction factor of the internal array conteining the RLUT. This
            is useful for large images.
            The factor should be >= 1.0.
            If it is == 1.0 a numpy array would be assumed and used directly,
            otherwise a RectBivariateSpline will be assumed in rlut_x1 and
            rlut_x2 to interpolate for the missing values on the reduced array.
        """
        assert(factor >= 1.0)
        if factor == 1.0:
            assert(rlut_x1.shape == rlut_x2.shape)
        self.rlut_x1 = rlut_x1
        self.rlut_x2 = rlut_x2
        self.proj = proj
        self.factor = factor

    def __call__(self, az, rg):
        """
        Converts the given az & rg positions to coordinates according to the
        RLUT tables.
        Broadcasting rules should apply.

        Parameters
        ----------

        az: int or array-like of ints
            Azimuth positions to get the coordinates.
            Should have the same size than the rg positions
        rg: int or array-like of ints
            Range positions to get the coordinates
            Should have the same size than the az positions
        """
        if self.factor != 1.0:
            return (self.rlut_x1.ev(az, rg), self.rlut_x2.ev(az, rg))
        else:
            # 'numpy.ndarray' object is not callable
            return (self.rlut_x1[az, rg], self.rlut_x2[az, rg])

    def to_coordinates(self, az, rg, dest_proj):
        """
        Converts the given az & rg positions to coordinates in the specified
        projection according to the RLUT tables.
        Broadcasting rules should apply.

        Parameters
        ----------

        az: int or array-like of ints
            Azimuth positions to get the coordinates.
            Should have the same size than the rg positions
        rg: int or array-like of ints
            Range positions to get the coordinates
            Should have the same size than the az positions
        dest_proj: pyproj.Proj
            Projection on which the pixel coordinates will be retrieved.
        """
        # Convert first to lat/lon and then to destination projection dest_proj
        ll = pyproj.Proj(proj='longlat', ellps='WGS84', datum='WGS84')
        p1, p2 = self(az, rg)
        p1, p2 = pyproj.transform(self.proj, ll, p1, p2)
        return pyproj.transform(ll, dest_proj, p1, p2)

    def get_Proj(self):
        """
        Returns the pyproj.Proj projection
        """
        return self.proj

    def to_npz_file(self, fname):
        """
        Save RLUT to a compressed .npz file.

        Parameters
        ----------
        fname: string
            Filename of the output file to write the RLUT.
        """
        np.savez_compressed(fname, rlut_x1=self.rlut_x1, rlut_x2=self.rlut_x2,
                        factor=self.factor,
                        proj_def=self.proj.definition_string())

    @classmethod
    def from_npz_file(cls, fname):
        """
        Loads an RLUT previously saved with rlut.to_npz_file()

        Parameters
        ----------
        fname: string
            The filename of the .npz file to load the LUT.
        """
        frlut = np.load(fname)
        labels = ['rlut_x1', 'rlut_x2', 'factor', 'proj_def']
        if np.alltrue([ label in frlut.files for label in labels]):
            return cls(rlut_x1=frlut['rlut_x1'], rlut_x2=frlut['rlut_x2'],
                       proj=pyproj.Proj(str(frlut['proj_def'])),
                       factor=frlut['factor'])
        else:
            raise ValueError("Invalid file. The file does not contain the required information to load the RLUT object!")


class LUT3D(object):
    """
    Class to represent the 3D Look Up Table (LUT) information of an image for
    3D geocoding.
    """
    def __init__(self, limits, lut_rg, lut_az, lut_3d_rg_o1, lut_3d_az_o1,
                 lut_3d_rg_o2, lut_3d_az_o2, lut_3d_h0,
                 proj_params=None):
        """
        Constructs the LUT with the given parameters.
        See also the from_*(...) class methods for LUT generation.

        Parameters
        ----------

        limits: array
            The limits (coordinates) of the LUT in the given projection.
            If 2 dimensions x1 and x2 are available, it should be:
            [min_x1, max_x1, min_x2, max_x2]

            NOTE: min and max corresponds to the *covered* coordinates value.
            This means that the min and max values corresponds to first and
            last pixels coordinates of the lut_rg and lut_az.
        lut_rg: array
            The range LUT array
        lut_az: array
            The azimuth LUT array
        lut_3d_rg_o1: array
            The range 3D LUT array for 1st polynomial coefficient
        lut_3d_az_o1: array
            The azimuth 3D LUT array for 1st polynomial coefficient
        lut_3d_rg_o2: array
            The range 3D LUT array for 2nd polynomial coefficient
        lut_3d_az_o2: array
            The azimuth 3D LUT array for 2nd polynomial coefficient
        lut_3d_h0: array
            The ellipsoidal reference heights used to compute the 2D LUT
        proj_params: dict
            The parameters that define the coordinates projection
            system according to pyproj.Proj library.
            If not specified, latitude & longitude coordinates over an WGS84
            ellipsoid are assumed
            (proj='latlong', ellps='WGS84', datum='WGS84').
        """
        assert(lut_rg.shape == lut_az.shape)
        assert(len(limits) == 4)
        self.min_x1 = limits[0]
        self.max_x1 = limits[1]
        self.min_x2 = limits[2]
        self.max_x2 = limits[3]
        self.c1 = np.array([limits[0], limits[2]])
        self.c2 = np.array([limits[1], limits[3]])
        shape = lut_rg.shape
        self.x1_step = (self.max_x1-self.min_x1) / (shape[0]-1)
        self.x2_step = (self.max_x2-self.min_x2) / (shape[1]-1)
        self.lut_rg = lut_rg
        self.lut_az = lut_az
        self.lut3d_o1_rg = lut_3d_rg_o1
        self.lut3d_o1_az = lut_3d_az_o1
        self.lut3d_o2_rg = lut_3d_rg_o2
        self.lut3d_o2_az = lut_3d_az_o2
        self.lut3d_h0 = lut_3d_h0
        # TODO: Check all arays have same shape
        self.proj_params=proj_params
        self.logger = logging.getLogger('LUT')
        if proj_params==None:
            # Default projection (lat/lon)
            self.proj = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
        else:
            self.proj = pyproj.Proj(**proj_params)

    def get_Proj(self):
        """
        Returns the pyproj.Proj projection
        """
        return self.proj

    def get_extent(self):
        """
        Obtains the extent of the covered area coordinates, that is, the
        minimum and maximum value for each of the coordinates.

        This is especially useful for plotting geocoded images:
            ```
            plt.imshow(geo_img, origin='lower', extent=lut.get_extent())
            ```

        Returns
        -------
        extend: ndarray, shape (4)

        """
        return np.array([self.min_x2, self.max_x2, self.min_x1, self.max_x1])

    def to_npz_file(self, fname):
        """
        Save to a compressed .npz file.

        Parameters
        ----------
        fname: string
            Filename of the output file to write the LUT.
        """
        np.savez_compressed(fname, lut_rg = self.lut_rg, lut_az = self.lut_az,
                        lut3d_o1_rg = self.lut3d_o1_rg,
                        lut3d_o1_az = self.lut3d_o1_az,
                        lut3d_o2_rg = self.lut3d_o2_rg,
                        lut3d_o2_az = self.lut3d_o2_az,
                        lut3d_h0 = self.lut3d_h0,
                        corners=np.array([self.c1, self.c2]),
                        proj_params=self.proj_params)

    def generate_LUT_at_height(self, height, relative_height=False,
                               min_valid_height=-999):
        """
        Gerate a LUT object at a given height. If height is an array it is
        assumed to be sampled on the same geographical grid and projection
        than the original LUT3D

        Parameters
        ----------
        height : float or array
            Relative height with respect to reference height (h0) or reference
            ellipsoid.
        relative_height : bool, optional, default=False
            If relative_height is True the height are relative to the
            reference height (h0). That means that a height of 0 corresponds
            to the reference height at which the 2D LUT has been computed.
            If relative_height is False the height are ellipsodal heights
            relative to the reference ellipsoid of the LUT.
        min_valid_height : int, optional, default=-999
            Minimum valid value of height. All values below this number will
            be considered as invalid. This is required to recognize invalid
            values in the provided height map.

        Returns
        -------
        lut: LUT object
            LUT for the given heigths

        Notes
        -------
        Only the intersection between the LUT valid points and the provided
        height valid points will be employed for the 3D LUT. The points where
        the provided height has a non-valid value (non-finite or below
        min_valid_height) a delta-height of 0 will be used, corresponding to
        the original LUT reference height.
        """
        msk_lut = np.isfinite(self.lut_az) & (self.lut_az >= 0)
        msk_height = np.isfinite(height) & (height >= min_valid_height)
        msk = msk_lut & msk_height
        delta_h = np.zeros_like(self.lut_az)
        if relative_height==True:
            delta_h[msk] = height[msk]
        else:
            delta_h[msk] = (height[msk] - self.lut3d_h0[msk])
        # Computing the LUT at the given height. See:
        # https://www.dlr.de/hr/en/desktopdefault.aspx/tabid-2326/3776_read-48006/
        # https://www.dlr.de/hr/Portaldata/32/Resources/images/institut/sar-technologie/f-sar/F-SAR_DIMS-products.pdf
        newlut_rg = (self.lut_rg + delta_h * self.lut3d_o1_rg
                  + delta_h**2 * self.lut3d_o2_rg)
        newlut_az = (self.lut_az + delta_h * self.lut3d_o1_az
                  + delta_h**2 * self.lut3d_o2_az)
        limits = [self.min_x1, self.max_x1, self.min_x2, self.max_x2]
        return LUT(limits, newlut_rg, newlut_az, self.proj_params)

    def get_axes_coordinates(self):
        """
        Returns the axes coordinates grid, according the projection of this
        LUT3D.

        Returns
        -------
        x1_range : array
            Coordinate values for the first dimension.
        x2_range : array
            Coordinate values for the second dimension.

        """
        x1_range = self.min_x1 + np.arange(self.lut_az.shape[0]) * self.x1_step
        x2_range = self.min_x2 + np.arange(self.lut_az.shape[1]) * self.x2_step
        return x1_range, x2_range


    @classmethod
    def from_npz_file(cls, fname):
        """
        Loads the LUT3D previously saved with lut3d.to_npz_file()

        Parameters
        ----------
        fname: string
            The filename of the .npz file to load the LUT3D.
        """
        flut = np.load(fname)
        if np.alltrue([ label in flut.files for label in ['corners', 'proj_params',
                                                          'lut_rg', 'lut_az',
                                                          'lut3d_o1_rg',
                                                          'lut3d_o1_az',
                                                          'lut3d_o2_rg',
                                                          'lut3d_o2_az',
                                                          'lut3d_h0',
                                                          ] ]):
            # New format
            c1 = flut['corners'][0]
            c2 = flut['corners'][1]
            # Note: to get a dictionary from npz use [()]
            # https://stackoverflow.com/questions/22315595/saving-dictionary-of-header-information-using-numpy-savez
            return cls([c1[0], c2[0], c1[1], c2[1]],
                       flut['lut_rg'], flut['lut_az'],
                       flut['lut_3d_rg_o1'], flut['lut_3d_az_o1'],
                       flut['lut_3d_rg_o2'], flut['lut_3d_az_o2'],
                       flut['lut_3d_h0'], flut['proj_params'][()])
        else:
            raise ValueError("Invalid file. The file does not contain the required information to load the LUT object!")

    @classmethod
    def from_FSAR_lut3d_utm_files(cls, fname_az, fname_rg,
                                fname3d_o1_az, fname3d_o1_rg,
                                fname3d_o2_az, fname3d_o2_rg,
                                fname3d_h0,
                                hdr_fname=None):
        """
        Loads the LUT3D from FSAR utm look up tables (in RAT format).

        Parameters
        ----------
        fname_az: string
            The filename of the azimuth LUT RAT file
        fname_rg: string
            The filename of the range LUT RAT file
        fname3d_o1_az: string
            The filename of the azimuth 3D LUT 1st polynomial coefficient
        fname3d_o1_rg: string
            The filename of the range 3D LUT 1st polynomial coefficient
        fname3d_o2_az: string
            The filename of the azimuth 3D LUT 2nd polynomial coefficient
        fname3d_o2_rg: string
            The filename of the range 3D LUT 2nd polynomial coefficient
        fname3d_h0: string
            The filename of the ellipsoidal reference heights used to compute
            the 2D LUT
        hdr_fname: string, optional
            The filename of the header (.hdr) file containing the information
            of the coordinates, spacing, etc.
            If a hdr_fname is provided, the information will be readed from
            there instead of from the RAT header.
        """
        f_az = RatFile(fname_az)
        f_rg = RatFile(fname_rg)
        f_az_o1 = RatFile(fname3d_o1_az)
        f_rg_o1 = RatFile(fname3d_o1_rg)
        f_az_o2 = RatFile(fname3d_o2_az)
        f_rg_o2 = RatFile(fname3d_o2_rg)
        f_h0 = RatFile(fname3d_h0)
        # Check both LUTs have same size
        assert(f_az._get_shape() == f_rg._get_shape())

        if hdr_fname == None:
            # Load params from RAT header (assuming both headers are equal)
            min_x1 = f_az.Header.Geo.min_north
            min_x2 = f_az.Header.Geo.min_east
            ps_x1 = f_az.Header.Geo.ps_north
            ps_x2 = f_az.Header.Geo.ps_east
            zone = f_az.Header.Geo.zone
            hemisphere = f_az.Header.Geo.hemisphere
            if zone < 0 and hemisphere == 2:
                # South hemisphere. Correct negative zone as it is already
                # indicated by hemisphere variable.
                zone = -zone
        else:
            # Load params from header file
            f = open(hdr_fname, 'r')
            for line in f:
                line_separate = line.split('=')
                variable = line_separate[0]
                if variable.strip() == 'min_easting':
                    min_x2 = float(line_separate[1])
                if variable.strip() == 'min_northing':
                    min_x1 = float(line_separate[1])
                if variable.strip() == 'pixel_spacing_east':
                    ps_x2 = float(line_separate[1])
                if variable.strip() == 'pixel_spacing_north':
                    ps_x1 = float(line_separate[1])
                if variable.strip() == 'projection_zone':
                    zone = int(line_separate[1])
                if variable.strip() == 'map info':
                    if line_separate[1].find('North') > 0:
                        hemisphere = 1
                    else:
                        hemisphere = 2
                # On header files it seems that 'North' is always set
                # even for southern hemisphere. The southern hemisphere
                # seems to be indicated by a negative zone value.
                if zone < 0:
                    hemisphere = 2
                    zone = -zone
            f.close()

        # Get shape from header
        shape = f_az._get_shape()
        # Calculate max coordinates
        max_x1 = min_x1 + (shape[0] - 1)*ps_x1
        max_x2 = min_x2 + (shape[1] - 1)*ps_x2
        # Generate the projection information
        proj_params = {}
        proj_params['proj'] = 'utm'
        proj_params['zone'] = zone
        # Assume WGS84 ellipsoid!
        proj_params['ellps'] = 'WGS84'
        if hemisphere == 2:
            proj_params['south'] = True
        else:
            # Assume north also if unspecified!
            proj_params['north'] = True

        return cls([min_x1, max_x1, min_x2, max_x2],
                   np.flipud(f_rg.mread()), np.flipud(f_az.mread()),
                   np.flipud(f_rg_o1.mread()), np.flipud(f_az_o1.mread()),
                   np.flipud(f_rg_o2.mread()), np.flipud(f_az_o2.mread()),
                   np.flipud(f_h0.mread()),
                   proj_params=proj_params)


