import numpy as np
import pathlib
import rasterio
import rasterio.crs
import rasterio.transform
import fsarcamp as fc
from fsarcamp import campaign_utils


class AFRISR16Campaign:
    def __init__(self, campaign_folder):
        """
        Data loader for SAR data for the AFRISR 2016 campaign.
        The `campaign_folder` path on the DLR-HR server as of April 2026:
        "/hrdss/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/AFRISAR/16AFRISR/"
        """
        self.name = "AFRISR 2016"
        self.campaign_folder = pathlib.Path(campaign_folder)
        # Mapping for the INF folder: pass_name & band -> master_name
        # Here, the default master_name is used in case there are more than one master.
        self._pass_band_to_master = {
            ("16afrisr0202", "L"): "16afrisr0502",
            ("16afrisr0202", "P"): "16afrisr0502",
            ("16afrisr0203", "L"): "16afrisr0502",
            ("16afrisr0203", "P"): "16afrisr0502",
            ("16afrisr0204", "L"): "16afrisr0502",
            ("16afrisr0204", "P"): "16afrisr0502",
            ("16afrisr0205", "L"): "16afrisr0502",
            ("16afrisr0205", "P"): "16afrisr0502",
            ("16afrisr0206", "L"): "16afrisr0502",
            ("16afrisr0206", "P"): "16afrisr0502",
            ("16afrisr0207", "L"): "16afrisr0502",
            ("16afrisr0207", "P"): "16afrisr0502",
            ("16afrisr0208", "L"): "16afrisr0502",
            ("16afrisr0208", "P"): "16afrisr0502",
            ("16afrisr0209", "L"): "16afrisr0502",
            ("16afrisr0209", "P"): "16afrisr0502",
            ("16afrisr0210", "L"): "16afrisr0502",
            ("16afrisr0210", "P"): "16afrisr0502",
            ("16afrisr0211", "L"): "16afrisr0502",
            ("16afrisr0211", "P"): "16afrisr0502",
            ("16afrisr0212", "L"): "16afrisr0502",
            ("16afrisr0212", "P"): "16afrisr0502",
            ("16afrisr0213", "L"): "16afrisr0502",
            ("16afrisr0213", "P"): "16afrisr0502",
            ("16afrisr0214", "L"): "16afrisr0502",
            ("16afrisr0214", "P"): "16afrisr0502",
            ("16afrisr0302", "L"): None,
            ("16afrisr0302", "P"): None,
            ("16afrisr0303", "L"): None,
            ("16afrisr0303", "P"): None,
            ("16afrisr0304", "L"): "16afrisr0602",
            ("16afrisr0304", "P"): "16afrisr0602",
            ("16afrisr0305", "L"): None,
            ("16afrisr0305", "P"): None,
            ("16afrisr0306", "L"): None,
            ("16afrisr0306", "P"): None,
            ("16afrisr0307", "L"): None,
            ("16afrisr0307", "P"): None,
            ("16afrisr0308", "L"): None,
            ("16afrisr0308", "P"): None,
            ("16afrisr0309", "L"): "16afrisr0602",
            ("16afrisr0309", "P"): "16afrisr0602",
            ("16afrisr0310", "L"): "16afrisr0602",
            ("16afrisr0310", "P"): "16afrisr0602",
            ("16afrisr0311", "L"): "16afrisr0602",
            ("16afrisr0311", "P"): "16afrisr0602",
            ("16afrisr0402", "L"): None,
            ("16afrisr0402", "P"): None,
            ("16afrisr0403", "L"): "16afrisr0402",
            ("16afrisr0403", "P"): "16afrisr0402",
            ("16afrisr0404", "L"): "16afrisr0402",
            ("16afrisr0404", "P"): "16afrisr0402",
            ("16afrisr0405", "L"): "16afrisr0402",
            ("16afrisr0405", "P"): "16afrisr0402",
            ("16afrisr0406", "L"): "16afrisr0402",
            ("16afrisr0406", "P"): "16afrisr0402",
            ("16afrisr0407", "L"): "16afrisr0402",
            ("16afrisr0407", "P"): "16afrisr0402",
            ("16afrisr0408", "L"): "16afrisr0402",
            ("16afrisr0408", "P"): "16afrisr0402",
            ("16afrisr0409", "L"): "16afrisr0402",
            ("16afrisr0409", "P"): "16afrisr0402",
            ("16afrisr0410", "L"): "16afrisr0402",
            ("16afrisr0410", "P"): "16afrisr0402",
            ("16afrisr0411", "L"): "16afrisr0402",
            ("16afrisr0411", "P"): "16afrisr0402",
            ("16afrisr0412", "L"): "16afrisr0402",
            ("16afrisr0412", "P"): "16afrisr0402",
            ("16afrisr0502", "L"): None,
            ("16afrisr0502", "P"): None,
            ("16afrisr0503", "L"): "16afrisr0502",
            ("16afrisr0503", "P"): "16afrisr0502",
            ("16afrisr0504", "L"): "16afrisr0502",
            ("16afrisr0504", "P"): "16afrisr0502",
            ("16afrisr0505", "L"): "16afrisr0502",
            ("16afrisr0505", "P"): "16afrisr0502",
            ("16afrisr0602", "L"): None,
            ("16afrisr0602", "P"): None,
            ("16afrisr0603", "L"): "16afrisr0602",
            ("16afrisr0603", "P"): "16afrisr0602",
            ("16afrisr0604", "L"): "16afrisr0602",
            ("16afrisr0604", "P"): "16afrisr0602",
            ("16afrisr0605", "L"): "16afrisr0602",
            ("16afrisr0605", "P"): "16afrisr0602",
            ("16afrisr0606", "L"): "16afrisr0602",
            ("16afrisr0606", "P"): "16afrisr0602",
            ("16afrisr0607", "L"): "16afrisr0602",
            ("16afrisr0607", "P"): "16afrisr0602",
            ("16afrisr0608", "L"): "16afrisr0602",
            ("16afrisr0608", "P"): "16afrisr0602",
            ("16afrisr0609", "L"): "16afrisr0602",
            ("16afrisr0609", "P"): "16afrisr0602",
            ("16afrisr0610", "L"): "16afrisr0602",
            ("16afrisr0610", "P"): "16afrisr0602",
            ("16afrisr0611", "L"): "16afrisr0602",
            ("16afrisr0611", "P"): "16afrisr0602",
            ("16afrisr0612", "L"): "16afrisr0602",
            ("16afrisr0612", "P"): "16afrisr0602",
            ("16afrisr0613", "L"): "16afrisr0602",
            ("16afrisr0613", "P"): "16afrisr0602",
            ("16afrisr0702", "L"): None,
            ("16afrisr0702", "P"): None,
            ("16afrisr0703", "L"): "16afrisr0708",
            ("16afrisr0703", "P"): "16afrisr0708",
            ("16afrisr0704", "L"): "16afrisr0708",
            ("16afrisr0704", "P"): "16afrisr0708",
            ("16afrisr0705", "L"): "16afrisr0702",
            ("16afrisr0705", "P"): "16afrisr0702",
            ("16afrisr0706", "L"): "16afrisr0708",
            ("16afrisr0706", "P"): "16afrisr0708",
            ("16afrisr0707", "L"): "16afrisr0702",
            ("16afrisr0707", "P"): "16afrisr0702",
            ("16afrisr0708", "L"): None,
            ("16afrisr0708", "P"): None,
            ("16afrisr0709", "L"): "16afrisr0702",
            ("16afrisr0709", "P"): "16afrisr0702",
            ("16afrisr0710", "L"): "16afrisr0708",
            ("16afrisr0710", "P"): "16afrisr0708",
            ("16afrisr0711", "L"): "16afrisr0702",
            ("16afrisr0711", "P"): "16afrisr0702",
            ("16afrisr0712", "L"): "16afrisr0708",
            ("16afrisr0712", "P"): "16afrisr0708",
            ("16afrisr0713", "L"): "16afrisr0702",
            ("16afrisr0713", "P"): "16afrisr0702",
            ("16afrisr0714", "L"): "16afrisr0708",
            ("16afrisr0714", "P"): "16afrisr0708",
            ("16afrisr0715", "L"): "16afrisr0702",
            ("16afrisr0715", "P"): "16afrisr0702",
            ("16afrisr0716", "L"): "16afrisr0702",
            ("16afrisr0716", "P"): "16afrisr0702",
            ("16afrisr0717", "L"): "16afrisr0702",
            ("16afrisr0717", "P"): "16afrisr0702",
            ("16afrisr0718", "L"): "16afrisr0702",
            ("16afrisr0718", "P"): "16afrisr0702",
            ("16afrisr0802", "L"): "16afrisr0502",
            ("16afrisr0802", "P"): "16afrisr0502",
            ("16afrisr0803", "L"): "16afrisr0502",
            ("16afrisr0803", "P"): "16afrisr0502",
            ("16afrisr0804", "L"): "16afrisr0502",
            ("16afrisr0804", "P"): "16afrisr0502",
            ("16afrisr0805", "L"): "16afrisr0502",
            ("16afrisr0805", "P"): "16afrisr0502",
            ("16afrisr0902", "L"): None,
            ("16afrisr0902", "P"): None,
            ("16afrisr0903", "L"): None,
            ("16afrisr0903", "P"): None,
            ("16afrisr0904", "L"): None,
            ("16afrisr0904", "P"): None,
            ("16afrisr0905", "L"): "16afrisr0602",
            ("16afrisr0905", "P"): "16afrisr0602",
            ("16afrisr0906", "L"): "16afrisr0902",
            ("16afrisr0906", "P"): "16afrisr0902",
            ("16afrisr0907", "L"): "16afrisr0903",
            ("16afrisr0907", "P"): "16afrisr0903",
            ("16afrisr0908", "L"): "16afrisr0904",
            ("16afrisr0908", "P"): "16afrisr0904",
            ("16afrisr0909", "L"): "16afrisr0602",
            ("16afrisr0909", "P"): "16afrisr0602",
            ("16afrisr0910", "L"): "16afrisr0902",
            ("16afrisr0910", "P"): "16afrisr0902",
            ("16afrisr0911", "L"): "16afrisr0903",
            ("16afrisr0911", "P"): "16afrisr0903",
            ("16afrisr0912", "L"): "16afrisr0904",
            ("16afrisr0912", "P"): "16afrisr0904",
            ("16afrisr0913", "L"): "16afrisr0602",
            ("16afrisr0913", "P"): "16afrisr0602",
            ("16afrisr0914", "L"): "16afrisr0902",
            ("16afrisr0914", "P"): "16afrisr0902",
            ("16afrisr0915", "L"): "16afrisr0602",
            ("16afrisr0915", "P"): "16afrisr0602",
            ("16afrisr1102", "L"): "16afrisr1107",
            ("16afrisr1102", "P"): "16afrisr1107",
            ("16afrisr1103", "L"): "16afrisr1107",
            ("16afrisr1103", "P"): "16afrisr1107",
            ("16afrisr1104", "L"): "16afrisr1107",
            ("16afrisr1104", "P"): "16afrisr1107",
            ("16afrisr1105", "L"): "16afrisr1107",
            ("16afrisr1105", "P"): "16afrisr1107",
            ("16afrisr1106", "L"): "16afrisr1107",
            ("16afrisr1106", "P"): "16afrisr1107",
            ("16afrisr1107", "L"): None,
            ("16afrisr1107", "P"): None,
            ("16afrisr1108", "L"): "16afrisr1107",
            ("16afrisr1108", "P"): "16afrisr1107",
            ("16afrisr1109", "L"): "16afrisr1107",
            ("16afrisr1109", "P"): "16afrisr1107",
            ("16afrisr1110", "L"): "16afrisr1107",
            ("16afrisr1110", "P"): "16afrisr1107",
            ("16afrisr1111", "L"): "16afrisr1107",
            ("16afrisr1111", "P"): "16afrisr1107",
            ("16afrisr1202", "L"): "16afrisr1206",
            ("16afrisr1202", "P"): "16afrisr1206",
            ("16afrisr1203", "L"): "16afrisr1206",
            ("16afrisr1203", "P"): "16afrisr1206",
            ("16afrisr1204", "L"): "16afrisr1206",
            ("16afrisr1204", "P"): "16afrisr1206",
            ("16afrisr1205", "L"): "16afrisr1206",
            ("16afrisr1205", "P"): "16afrisr1206",
            ("16afrisr1206", "L"): None,
            ("16afrisr1206", "P"): None,
            ("16afrisr1207", "L"): "16afrisr1206",
            ("16afrisr1207", "P"): "16afrisr1206",
            ("16afrisr1208", "L"): "16afrisr1206",
            ("16afrisr1208", "P"): "16afrisr1206",
            ("16afrisr1209", "L"): "16afrisr1206",
            ("16afrisr1209", "P"): "16afrisr1206",
            ("16afrisr1210", "L"): "16afrisr1206",
            ("16afrisr1210", "P"): "16afrisr1206",
            ("16afrisr1302", "L"): "16afrisr1307",
            ("16afrisr1302", "P"): "16afrisr1307",
            ("16afrisr1303", "L"): "16afrisr1307",
            ("16afrisr1303", "P"): "16afrisr1307",
            ("16afrisr1304", "L"): "16afrisr1307",
            ("16afrisr1304", "P"): "16afrisr1307",
            ("16afrisr1305", "L"): "16afrisr1307",
            ("16afrisr1305", "P"): "16afrisr1307",
            ("16afrisr1307", "L"): None,
            ("16afrisr1307", "P"): None,
            ("16afrisr1308", "L"): "16afrisr1307",
            ("16afrisr1308", "P"): "16afrisr1307",
            ("16afrisr1309", "L"): "16afrisr1307",
            ("16afrisr1309", "P"): "16afrisr1307",
            ("16afrisr1310", "L"): "16afrisr1307",
            ("16afrisr1310", "P"): "16afrisr1307",
            ("16afrisr1311", "L"): "16afrisr1307",
            ("16afrisr1311", "P"): "16afrisr1307",
            ("16afrisr1402", "L"): "16afrisr0708",
            ("16afrisr1402", "P"): "16afrisr0708",
            ("16afrisr1403", "L"): "16afrisr0708",
            ("16afrisr1403", "P"): "16afrisr0708",
            ("16afrisr1404", "L"): "16afrisr0708",
            ("16afrisr1404", "P"): "16afrisr0708",
            ("16afrisr1405", "L"): "16afrisr0708",
            ("16afrisr1405", "P"): "16afrisr0708",
            ("16afrisr1406", "L"): "16afrisr0708",
            ("16afrisr1406", "P"): "16afrisr0708",
            ("16afrisr1407", "L"): "16afrisr0708",
            ("16afrisr1407", "P"): "16afrisr0708",
            ("16afrisr1408", "L"): "16afrisr0708",
            ("16afrisr1408", "P"): "16afrisr0708",
            ("16afrisr1409", "L"): "16afrisr0708",
            ("16afrisr1409", "P"): "16afrisr0708",
            ("16afrisr1410", "L"): "16afrisr0708",
            ("16afrisr1410", "P"): "16afrisr0708",
            ("16afrisr1411", "L"): "16afrisr0708",
            ("16afrisr1411", "P"): "16afrisr0708",
        }

    def get_pass(self, pass_name, band):
        master_name = self._pass_band_to_master.get((pass_name, band), None)
        return AFRISR16Pass(self.campaign_folder, pass_name, band, master_name)

    def get_all_pass_names(self, band):
        pass_names = [pass_name for pass_name, ps_b in self._pass_band_to_master.keys() if ps_b == band]
        return sorted(list(set(pass_names)))  # sort and de-duplicate


class AFRISR16Pass:
    def __init__(self, campaign_folder, pass_name, band, master_name=None):
        self.campaign_folder = pathlib.Path(campaign_folder)
        self.pass_name = pass_name
        self.band = band
        self.master_name = master_name

    # RGI folder

    def load_rgi_slc(self, pol):
        """
        Load SLC in specified polarization ("hh", "hv", "vh", "vv") from the RGI folder.
        """
        try_name = self._get_try_name()
        return fc.mrrat(self._get_rgi_folder() / "RGI-SR" / f"slc_{self.pass_name}_{self.band}{pol}_{try_name}.rat")

    def load_rgi_incidence(self, pol=None):
        """
        Load incidence angle from the RGI folder.
        Polarization is ignored for the AFRISR 2016 campaign.
        """
        try_name = self._get_try_name()
        return fc.mrrat(self._get_rgi_folder() / "RGI-SR" / f"incidence_{self.pass_name}_{self.band}_{try_name}.rat")

    def load_rgi_mask(self, pol=None):
        """
        Load the mask from the RGI folder.
        Polarization is ignored for the AFRISR 2016 campaign.
        """
        try_name = self._get_try_name()
        return fc.mrrat(self._get_rgi_folder() / "RGI-SR" / f"mask_{self.pass_name}_{self.band}_{try_name}.rat")
    
    def load_rgi_params(self, pol="hh"):
        """
        Load radar parameters from the RGI folder. Default polarization is "hh".
        """
        try_name = self._get_try_name()
        return campaign_utils.parse_xml_parameters(
            self._get_rgi_folder() / "RGI-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_{try_name}.xml"
        )

    # INF folder

    def load_inf_slc(self, pol):
        """
        Load coregistered SLC in specified polarization ("hh", "hv", "vh", "vv") from the INF folder.
        """
        try_name = self._get_try_name()
        return fc.mrrat(
            self._get_inf_folder()
            / "INF-SR"
            / f"slc_coreg_{self.master_name}_{self.pass_name}_{self.band}{pol}_{try_name}.rat"
        )

    def load_inf_pha_dem(self, pol=None):
        """
        Load interferometric phase correction derived from track and terrain geometry.
        The residual can be used to correct the phase of the coregistered SLCs: coreg_slc * np.exp(1j * phase)
        This is equivalent of subtracting the phase from the interferogram.
        Polarization is ignored for the AFRISR 2016 campaign.
        """
        try_name = self._get_try_name()
        return fc.mrrat(
            self._get_inf_folder()
            / "INF-SR"
            / f"pha_dem_{self.master_name}_{self.pass_name}_{self.band}_{try_name}.rat"
        )

    def load_inf_pha_fe(self, pol=None):
        """
        Load interferometric flat-Earth phase.
        For the AFRISR 2016 campaign, this phase is included into pha_dem and pha_fe is 0.
        This method exists only for compatibility with older campaigns and returns a hard-coded 0.
        """
        return 0

    def load_inf_kz(self, pol):
        """
        Load interferometric kz.
        """
        try_name = self._get_try_name()
        return fc.mrrat(
            self._get_inf_folder()
            / "INF-SR"
            / f"kz_{self.master_name}_{self.pass_name}_{self.band}{pol}_{try_name}.rat"
        )
    
    # No INF masks available for the AFRISR 2016 campaign

    def load_inf_params(self, pol="hh"):
        """
        Load radar parameters from the INF folder. Default polarization is "hh".
        """
        try_name = self._get_try_name()
        return campaign_utils.parse_xml_parameters(
            self._get_inf_folder() / "INF-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_{try_name}.xml"
        )

    def load_inf_insar_params(self, pol="hh"):
        """
        Load insar radar parameters from the INF folder. Default polarization is "hh".
        """
        try_name = self._get_try_name()
        return campaign_utils.parse_xml_parameters(
            self._get_inf_folder()
            / "INF-RDP"
            / f"ppinsar_{self.master_name}_{self.pass_name}_{self.band}{pol}_{try_name}.xml"
        )

    # GTC folder

    def load_gtc_sr2geo_lut(self):
        try_name = self._get_try_name()
        lut_az_path = (
            self._get_nested_gtc_folder() / "GTC-LUT" / f"sr2geo_az_{self.pass_name}_{self.band}_{try_name}.rat"
        )
        lut_rg_path = (
            self._get_nested_gtc_folder() / "GTC-LUT" / f"sr2geo_rg_{self.pass_name}_{self.band}_{try_name}.rat"
        )
        # read lookup tables
        f_az = fc.RatFile(lut_az_path)
        f_rg = fc.RatFile(lut_rg_path)
        # in the RAT file northing (first axis) is decreasing, and easting (second axis) is increasing
        lut_az = f_az.mread()  # reading with memory map: fast and read-only
        lut_rg = f_rg.mread()
        assert lut_az.shape == lut_rg.shape
        # read projection
        header_geo = f_az.Header.Geo  # assume lut az and lut rg headers are equal
        hemisphere_key = "south" if header_geo.hemisphere == 2 else "north"
        proj_params = {
            "proj": "utm",
            "zone": np.abs(header_geo.zone),  # negative zone indicates southern hemisphere (defined separaterly)
            "ellps": "WGS84",  # assume WGS84 ellipsoid
            hemisphere_key: True,
        }
        crs = rasterio.crs.CRS.from_dict(proj_params)
        # get affine transform
        ps_north = header_geo.ps_north
        ps_east = header_geo.ps_east
        min_north = header_geo.min_north
        min_east = header_geo.min_east
        max_north = min_north + ps_north * (lut_az.shape[0] - 1)
        transform = rasterio.transform.from_origin(min_east, max_north, ps_east, ps_north)
        lut = fc.SlantRange2Geo(lut_az=lut_az, lut_rg=lut_rg, crs=crs, transform=transform)
        return lut

    def _read_sr2latlon_header(self, path):
        # Load params from header file
        f = open(path, "r")
        param_dict = {}
        parse_variables = set(["lon_min", "lon_max", "lat_min", "lat_max"])
        for line in f:
            var_val = line.split("=")
            if len(var_val) != 2:
                continue
            variable, value = var_val
            variable = variable.strip()
            if variable in parse_variables:
                param_dict[variable] = float(value)
        return param_dict

    def load_gtc_sr2latlon_lut(self):
        try_name = self._get_try_name()
        gtc_lut = self._get_nested_gtc_folder() / "GTC-LUT"
        lut_az_path = gtc_lut / f"sr2latlon_az_{self.pass_name}_{self.band}_{try_name}.rat"
        lut_rg_path = gtc_lut / f"sr2latlon_rg_{self.pass_name}_{self.band}_{try_name}.rat"
        hdr_az_path = gtc_lut / f"sr2latlon_az_{self.pass_name}_{self.band}_{try_name}.rat.hdr"
        # read lookup tables
        f_az = fc.RatFile(lut_az_path)
        f_rg = fc.RatFile(lut_rg_path)
        header = self._read_sr2latlon_header(hdr_az_path)
        # reading with memory map: fast and read-only
        lut_az = f_az.mread()
        lut_rg = f_rg.mread()
        # flip image updown, to be consistent with sr2geo
        lut_az = np.flipud(lut_az)
        lut_rg = np.flipud(lut_rg)
        assert lut_az.shape == lut_rg.shape
        crs = rasterio.crs.CRS.from_epsg(4326)
        lon_min = header["lon_min"]
        lon_max = header["lon_max"]
        lat_min = header["lat_min"]
        lat_max = header["lat_max"]
        rows, cols = lut_az.shape
        transform = rasterio.transform.from_bounds(lon_min, lat_min, lon_max, lat_max, cols, rows)
        lut = fc.SlantRange2Geo(lut_az=lut_az, lut_rg=lut_rg, crs=crs, transform=transform)
        return lut

    # Helpers

    def _get_try_name(self):
        return "tL02" if self.band == "L" else "tP01"

    def _get_rgi_folder(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        try_folder = self._get_try_name().upper()
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/{try_folder}/RGI"

    def _get_inf_folder(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        try_folder = self._get_try_name().upper()
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/{try_folder}/INF"

    def _get_gtc_folder(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        try_folder = self._get_try_name().upper()
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/{try_folder}/GTC"

    def _get_nested_gtc_folder(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        try_folder = self._get_try_name().upper()
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/{try_folder}/GTC/GTC"
