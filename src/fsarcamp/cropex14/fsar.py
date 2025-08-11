import numpy as np
import pathlib
import rasterio
import rasterio.crs
import rasterio.transform
import fsarcamp as fc
from fsarcamp import campaign_utils


class CROPEX14Campaign:
    def __init__(self, campaign_folder):
        """
        Data loader for SAR data for the CROPEX 2014 campaign.
        The `campaign_folder` path on the DLR-HR server as of August 2025:
        "/hrdss/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/CROPEX/CROPEX14"
        """
        self.name = "CROPEX 2014"
        self.campaign_folder = pathlib.Path(campaign_folder)
        # Mapping for the INF folder: pass_name & band -> master_name
        # Here, the default master_name is used in case there are more than one master.
        self._pass_band_to_master = {
            ("14cropex0102", "C"): None,
            ("14cropex0102", "X"): None,
            ("14cropex0103", "C"): "14cropex0102",
            ("14cropex0103", "X"): "14cropex0102",
            ("14cropex0105", "X"): "14cropex0102",
            ("14cropex0106", "C"): "14cropex0102",
            ("14cropex0106", "X"): "14cropex0102",
            ("14cropex0202", "C"): "14cropex0203",
            ("14cropex0202", "X"): "14cropex0203",
            ("14cropex0203", "C"): None,
            ("14cropex0203", "X"): None,
            ("14cropex0204", "C"): "14cropex0203",
            ("14cropex0204", "X"): "14cropex0203",
            ("14cropex0206", "X"): "14cropex0203",
            ("14cropex0209", "L"): "14cropex0210",
            ("14cropex0210", "L"): None,
            ("14cropex0211", "L"): "14cropex0210",
            ("14cropex0302", "L"): "14cropex0305",
            ("14cropex0303", "L"): "14cropex0305",
            ("14cropex0304", "L"): "14cropex0305",
            ("14cropex0305", "L"): None,
            ("14cropex0306", "L"): "14cropex0305",
            ("14cropex0307", "L"): "14cropex0305",
            ("14cropex0308", "L"): "14cropex0305",
            ("14cropex0309", "L"): "14cropex0305",
            ("14cropex0311", "C"): "14cropex0316",
            ("14cropex0311", "X"): "14cropex0316",
            ("14cropex0312", "C"): "14cropex0316",
            ("14cropex0312", "X"): "14cropex0316",
            ("14cropex0313", "C"): "14cropex0316",
            ("14cropex0313", "X"): "14cropex0316",
            ("14cropex0314", "C"): "14cropex0316",
            ("14cropex0314", "X"): "14cropex0316",
            ("14cropex0315", "C"): "14cropex0316",
            ("14cropex0315", "X"): "14cropex0316",
            ("14cropex0316", "C"): None,
            ("14cropex0316", "X"): None,
            ("14cropex0317", "C"): "14cropex0316",
            ("14cropex0317", "X"): "14cropex0316",
            ("14cropex0318", "C"): "14cropex0316",
            ("14cropex0318", "X"): "14cropex0316",
            ("14cropex0319", "C"): "14cropex0316",
            ("14cropex0319", "X"): "14cropex0316",
            ("14cropex0321", "X"): "14cropex0316",
            ("14cropex0402", "C"): None,
            ("14cropex0402", "X"): None,
            ("14cropex0403", "C"): "14cropex0402",
            ("14cropex0403", "X"): "14cropex0402",
            ("14cropex0404", "X"): "14cropex0402",
            ("14cropex0502", "X"): "14cropex0504",
            ("14cropex0504", "C"): None,
            ("14cropex0504", "X"): None,
            ("14cropex0505", "C"): "14cropex0504",
            ("14cropex0505", "X"): "14cropex0504",
            ("14cropex0604", "C"): "14cropex0610",
            ("14cropex0604", "X"): "14cropex0610",
            ("14cropex0605", "C"): "14cropex0610",
            ("14cropex0605", "X"): "14cropex0610",
            ("14cropex0606", "C"): "14cropex0610",
            ("14cropex0606", "X"): "14cropex0610",
            ("14cropex0607", "C"): "14cropex0610",
            ("14cropex0607", "X"): "14cropex0610",
            ("14cropex0608", "C"): "14cropex0610",
            ("14cropex0608", "X"): "14cropex0610",
            ("14cropex0609", "C"): "14cropex0610",
            ("14cropex0609", "X"): "14cropex0610",
            ("14cropex0610", "C"): None,
            ("14cropex0610", "X"): None,
            ("14cropex0611", "C"): "14cropex0610",
            ("14cropex0611", "X"): "14cropex0610",
            ("14cropex0612", "C"): "14cropex0610",
            ("14cropex0612", "X"): "14cropex0610",
            ("14cropex0615", "X"): "14cropex0610",
            ("14cropex0618", "L"): "14cropex0620",
            ("14cropex0619", "L"): "14cropex0620",
            ("14cropex0620", "L"): None,
            ("14cropex0621", "L"): "14cropex0620",
            ("14cropex0622", "L"): "14cropex0620",
            ("14cropex0623", "L"): "14cropex0620",
            ("14cropex0702", "X"): "14cropex0708",
            ("14cropex0704", "C"): "14cropex0708",
            ("14cropex0704", "X"): "14cropex0708",
            ("14cropex0705", "C"): "14cropex0708",
            ("14cropex0705", "X"): "14cropex0708",
            ("14cropex0706", "C"): "14cropex0708",
            ("14cropex0706", "X"): "14cropex0708",
            ("14cropex0707", "C"): "14cropex0708",
            ("14cropex0707", "X"): "14cropex0708",
            ("14cropex0708", "C"): None,
            ("14cropex0708", "X"): None,
            ("14cropex0709", "C"): "14cropex0708",
            ("14cropex0709", "X"): "14cropex0708",
            ("14cropex0710", "C"): "14cropex0708",
            ("14cropex0710", "X"): "14cropex0708",
            ("14cropex0711", "C"): "14cropex0708",
            ("14cropex0711", "X"): "14cropex0708",
            ("14cropex0712", "C"): "14cropex0708",
            ("14cropex0712", "X"): "14cropex0708",
            ("14cropex0714", "L"): "14cropex0718",
            ("14cropex0715", "L"): "14cropex0718",
            ("14cropex0716", "L"): "14cropex0718",
            ("14cropex0717", "L"): "14cropex0718",
            ("14cropex0718", "L"): None,
            ("14cropex0719", "L"): "14cropex0718",
            ("14cropex0720", "L"): "14cropex0718",
            ("14cropex0802", "X"): "14cropex0804",
            ("14cropex0804", "C"): None,
            ("14cropex0804", "X"): None,
            ("14cropex0805", "C"): None,
            ("14cropex0805", "X"): None,
            ("14cropex0806", "C"): "14cropex0804",
            ("14cropex0806", "X"): "14cropex0804",
            ("14cropex0902", "X"): "14cropex0904",
            ("14cropex0904", "C"): None,
            ("14cropex0904", "X"): None,
            ("14cropex0905", "C"): "14cropex0904",
            ("14cropex0905", "X"): "14cropex0904",
            ("14cropex0906", "C"): "14cropex0904",
            ("14cropex0906", "X"): "14cropex0904",
            ("14cropex0907", "C"): "14cropex0904",
            ("14cropex0907", "X"): "14cropex0904",
            ("14cropex0908", "C"): "14cropex0904",
            ("14cropex0908", "X"): "14cropex0904",
            ("14cropex0909", "C"): "14cropex0904",
            ("14cropex0909", "X"): "14cropex0904",
            ("14cropex0910", "C"): "14cropex0904",
            ("14cropex0910", "X"): "14cropex0904",
            ("14cropex0911", "C"): "14cropex0904",
            ("14cropex0911", "X"): "14cropex0904",
            ("14cropex0912", "C"): "14cropex0904",
            ("14cropex0912", "X"): "14cropex0904",
            ("14cropex0914", "L"): None,
            ("14cropex0915", "L"): "14cropex0914",
            ("14cropex0916", "L"): "14cropex0914",
            ("14cropex0917", "L"): "14cropex0914",
            ("14cropex0918", "L"): "14cropex0914",
            ("14cropex0919", "L"): "14cropex0914",
            ("14cropex0920", "L"): "14cropex0914",
            ("14cropex1002", "C"): "14cropex1003",
            ("14cropex1002", "X"): "14cropex1003",
            ("14cropex1003", "C"): None,
            ("14cropex1003", "X"): None,
            ("14cropex1004", "C"): "14cropex1003",
            ("14cropex1004", "X"): "14cropex1003",
            ("14cropex1006", "X"): "14cropex1003",
            ("14cropex1102", "X"): "14cropex1104",
            ("14cropex1104", "C"): None,
            ("14cropex1104", "X"): None,
            ("14cropex1105", "C"): "14cropex1104",
            ("14cropex1105", "X"): "14cropex1104",
            ("14cropex1106", "C"): "14cropex1104",
            ("14cropex1106", "X"): "14cropex1104",
            ("14cropex1107", "C"): "14cropex1104",
            ("14cropex1107", "X"): "14cropex1104",
            ("14cropex1108", "C"): "14cropex1104",
            ("14cropex1108", "X"): "14cropex1104",
            ("14cropex1109", "C"): "14cropex1104",
            ("14cropex1109", "X"): "14cropex1104",
            ("14cropex1110", "C"): "14cropex1104",
            ("14cropex1110", "X"): "14cropex1104",
            ("14cropex1111", "C"): "14cropex1104",
            ("14cropex1111", "X"): "14cropex1104",
            ("14cropex1112", "C"): "14cropex1104",
            ("14cropex1112", "X"): "14cropex1104",
            ("14cropex1114", "L"): None,
            ("14cropex1115", "L"): "14cropex1114",
            ("14cropex1116", "L"): "14cropex1114",
            ("14cropex1117", "L"): "14cropex1114",
            ("14cropex1118", "L"): "14cropex1114",
            ("14cropex1119", "L"): "14cropex1114",
            ("14cropex1120", "L"): "14cropex1114",
            ("14cropex1121", "L"): "14cropex1114",
            ("14cropex1203", "C"): None,
            ("14cropex1203", "X"): None,
            ("14cropex1204", "C"): "14cropex1203",
            ("14cropex1204", "X"): "14cropex1203",
            ("14cropex1205", "C"): "14cropex1203",
            ("14cropex1205", "X"): "14cropex1203",
            ("14cropex1206", "C"): "14cropex1203",
            ("14cropex1206", "X"): "14cropex1203",
            ("14cropex1208", "X"): "14cropex1203",
            ("14cropex1210", "X"): "14cropex1203",
            ("14cropex1305", "X"): "14cropex1307",
            ("14cropex1307", "C"): None,
            ("14cropex1307", "X"): None,
            ("14cropex1308", "C"): "14cropex1307",
            ("14cropex1308", "X"): "14cropex1307",
            ("14cropex1309", "C"): "14cropex1307",
            ("14cropex1309", "X"): "14cropex1307",
            ("14cropex1310", "C"): "14cropex1307",
            ("14cropex1310", "X"): "14cropex1307",
            ("14cropex1312", "C"): "14cropex1307",
            ("14cropex1312", "X"): "14cropex1307",
            ("14cropex1313", "C"): "14cropex1307",
            ("14cropex1313", "X"): "14cropex1307",
            ("14cropex1314", "C"): "14cropex1307",
            ("14cropex1314", "X"): "14cropex1307",
            ("14cropex1315", "C"): "14cropex1307",
            ("14cropex1315", "X"): "14cropex1307",
            ("14cropex1316", "C"): "14cropex1307",
            ("14cropex1316", "X"): "14cropex1307",
            ("14cropex1318", "L"): None,
            ("14cropex1319", "L"): "14cropex1318",
            ("14cropex1320", "L"): "14cropex1318",
            ("14cropex1321", "L"): "14cropex1318",
            ("14cropex1322", "L"): "14cropex1318",
            ("14cropex1323", "L"): "14cropex1318",
            ("14cropex1324", "L"): "14cropex1318",
            ("14cropex1402", "C"): None,
            ("14cropex1402", "X"): None,
            ("14cropex1403", "C"): "14cropex1402",
            ("14cropex1403", "X"): "14cropex1402",
            ("14cropex1405", "X"): "14cropex1402",
            ("14cropex1502", "C"): None,
            ("14cropex1502", "X"): None,
            ("14cropex1503", "C"): None,
            ("14cropex1503", "X"): None,
            ("14cropex1504", "C"): None,
            ("14cropex1504", "X"): None,
            ("14cropex1505", "C"): "14cropex1503",
            ("14cropex1505", "X"): "14cropex1503",
            ("14cropex1506", "C"): "14cropex1504",
            ("14cropex1506", "X"): "14cropex1504",
            ("14cropex1507", "C"): "14cropex1503",
            ("14cropex1507", "X"): "14cropex1503",
            ("14cropex1508", "C"): "14cropex1504",
            ("14cropex1508", "X"): "14cropex1504",
            ("14cropex1509", "C"): "14cropex1503",
            ("14cropex1509", "X"): "14cropex1503",
            ("14cropex1510", "C"): "14cropex1504",
            ("14cropex1510", "X"): "14cropex1504",
            ("14cropex1511", "C"): "14cropex1503",
            ("14cropex1511", "X"): "14cropex1503",
            ("14cropex1512", "C"): "14cropex1504",
            ("14cropex1512", "X"): "14cropex1504",
            ("14cropex1513", "C"): "14cropex1503",
            ("14cropex1513", "X"): "14cropex1503",
            ("14cropex1622", "L"): None,
        }

    def get_pass(self, pass_name, band):
        master_name = self._pass_band_to_master.get((pass_name, band), None)
        return CROPEX14Pass(self.campaign_folder, pass_name, band, master_name)

    def get_all_pass_names(self, band):
        pass_names = [pass_name for pass_name, ps_b in self._pass_band_to_master.keys() if ps_b == band]
        return sorted(list(set(pass_names)))  # sort and de-duplicate
 

class CROPEX14Pass:
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
        pass_folder = self._get_pass_try_folder()
        return fc.mrrat(pass_folder / "RGI" / "RGI-SR" / f"slc_{self.pass_name}_{self.band}{pol}_t01.rat")

    def load_rgi_incidence(self, pol=None):
        """
        Load incidence angle from the RGI folder.
        Polarization is ignored for the CROPEX 14 campaign.
        """
        pass_folder = self._get_pass_try_folder()
        return fc.mrrat(pass_folder / "RGI" / "RGI-SR" / f"incidence_{self.pass_name}_{self.band}_t01.rat")

    def load_rgi_params(self, pol="hh"):
        """
        Load radar parameters from the RGI folder. Default polarization is "hh".
        """
        pass_folder = self._get_pass_try_folder()
        return campaign_utils.parse_xml_parameters(
            pass_folder / "RGI" / "RGI-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_t01.xml"
        )

    # INF folder

    def load_inf_slc(self, pol):
        """
        Load coregistered SLC in specified polarization ("hh", "hv", "vh", "vv") from the INF folder.
        """
        pass_folder = self._get_pass_try_folder()
        return fc.mrrat(
            pass_folder / "INF" / "INF-SR" / f"slc_coreg_{self.master_name}_{self.pass_name}_{self.band}{pol}_t01.rat"
        )

    def load_inf_pha_dem(self, pol=None):
        """
        Load interferometric phase correction derived from track and terrain geometry.
        The residual can be used to correct the phase of the coregistered SLCs: coreg_slc * np.exp(1j * phase)
        This is equivalent of subtracting the phase from the interferogram.
        """
        pass_folder = self._get_pass_try_folder()
        return fc.mrrat(
            pass_folder / "INF" / "INF-SR" / f"pha_dem_{self.master_name}_{self.pass_name}_{self.band}{pol}_t01.rat"
        )

    def load_inf_pha_fe(self, pol=None):
        """
        Load interferometric flat-Earth phase.
        The residual can be used to correct the phase of the coregistered SLCs: coreg_slc * np.exp(1j * phase)
        """
        pass_folder = self._get_pass_try_folder()
        return fc.mrrat(
            pass_folder / "INF" / "INF-SR" / f"pha_fe_{self.master_name}_{self.pass_name}_{self.band}{pol}_t01.rat"
        )

    def load_inf_kz(self, pol):
        """
        Load interferometric kz.
        """
        pass_folder = self._get_pass_try_folder()
        return fc.mrrat(
            pass_folder / "INF" / "INF-SR" / f"kz_{self.master_name}_{self.pass_name}_{self.band}{pol}_t01.rat"
        )

    def load_inf_params(self, pol="hh"):
        """
        Load radar parameters from the INF folder. Default polarization is "hh".
        """
        pass_folder = self._get_pass_try_folder()
        return campaign_utils.parse_xml_parameters(
            pass_folder / "INF" / "INF-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_t01.xml"
        )

    def load_inf_insar_params(self, pol="hh"):
        """
        Load insar radar parameters from the INF folder. Default polarization is "hh".
        """
        pass_folder = self._get_pass_try_folder()
        return campaign_utils.parse_xml_parameters(
            pass_folder / "INF" / "INF-RDP" / f"ppinsar_{self.master_name}_{self.pass_name}_{self.band}{pol}_t01.xml"
        )

    # GTC folder

    def load_gtc_sr2geo_lut(self):
        pass_folder = self._get_pass_try_folder()
        fname_lut_az = pass_folder / "GTC" / "GTC-LUT" / f"sr2geo_az_{self.pass_name}_{self.band}_t01.rat"
        fname_lut_rg = pass_folder / "GTC" / "GTC-LUT" / f"sr2geo_rg_{self.pass_name}_{self.band}_t01.rat"
        # read lookup tables
        f_az = fc.RatFile(fname_lut_az)
        f_rg = fc.RatFile(fname_lut_rg)
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

    # Helpers

    def _get_pass_try_folder(self):
        """The CROPEX 14 campaign has try folder "T01" for all passes."""
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/T01"

    def __repr__(self):
        return f"{self.pass_name}_{self.band}"
