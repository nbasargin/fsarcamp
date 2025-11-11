import numpy as np
import pathlib
import rasterio
import rasterio.crs
import rasterio.transform
import fsarcamp as fc
from fsarcamp import campaign_utils


class GABONX23Campaign:
    def __init__(self, campaign_folder):
        """
        Data loader for SAR data for the GABONX 2023 campaign.
        The `campaign_folder` path on the DLR-HR server as of November 2025:
        "/hrdss/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/23GABONX/"
        """
        self.name = "GABONX 2023"
        self.campaign_folder = pathlib.Path(campaign_folder)
        # Mapping for the INF folder: pass_name & band -> master_name
        # Here, the default master_name is used in case there are more than one master.
        self._pass_band_to_master = {
            ("23gabonx0204", "L"): "16afrisr0502",
            ("23gabonx0204", "P"): "16afrisr0502",
            ("23gabonx0205", "L"): "16afrisr0502",
            ("23gabonx0205", "P"): "16afrisr0502",
            ("23gabonx0206", "L"): "16afrisr0502",
            ("23gabonx0206", "P"): "16afrisr0502",
            ("23gabonx0207", "L"): "16afrisr0502",
            ("23gabonx0207", "P"): "16afrisr0502",
            ("23gabonx0208", "L"): "16afrisr0502",
            ("23gabonx0208", "P"): "16afrisr0502",
            ("23gabonx0209", "L"): "16afrisr0502",
            ("23gabonx0209", "P"): "16afrisr0502",
            ("23gabonx0210", "L"): "16afrisr0502",
            ("23gabonx0210", "P"): "16afrisr0502",
            ("23gabonx0211", "L"): "16afrisr0502",
            ("23gabonx0211", "P"): "16afrisr0502",
            ("23gabonx0212", "L"): "16afrisr0502",
            ("23gabonx0212", "P"): "16afrisr0502",
            ("23gabonx0213", "L"): "16afrisr0502",
            ("23gabonx0213", "P"): "16afrisr0502",
            ("23gabonx0214", "L"): "16afrisr0502",
            ("23gabonx0214", "P"): "16afrisr0502",
            ("23gabonx0215", "L"): "16afrisr0502",
            ("23gabonx0215", "P"): "16afrisr0502",
            ("23gabonx0302", "L"): None,
            ("23gabonx0302", "P"): None,
            ("23gabonx0303", "L"): "23gabonx0302",
            ("23gabonx0303", "P"): "23gabonx0302",
            ("23gabonx0304", "L"): "23gabonx0302",
            ("23gabonx0304", "P"): "23gabonx0302",
            ("23gabonx0305", "L"): "23gabonx0302",
            ("23gabonx0305", "P"): "23gabonx0302",
            ("23gabonx0306", "L"): "23gabonx0302",
            ("23gabonx0306", "P"): "23gabonx0302",
            ("23gabonx0307", "L"): "23gabonx0302",
            ("23gabonx0307", "P"): "23gabonx0302",
            ("23gabonx0308", "L"): "23gabonx0302",
            ("23gabonx0308", "P"): "23gabonx0302",
            ("23gabonx0309", "L"): "23gabonx0302",
            ("23gabonx0309", "P"): "23gabonx0302",
            ("23gabonx0310", "L"): "23gabonx0302",
            ("23gabonx0310", "P"): "23gabonx0302",
            ("23gabonx0311", "L"): "23gabonx0302",
            ("23gabonx0311", "P"): "23gabonx0302",
            ("23gabonx0312", "L"): "23gabonx0302",
            ("23gabonx0312", "P"): "23gabonx0302",
            ("23gabonx0313", "L"): "23gabonx0302",
            ("23gabonx0313", "P"): "23gabonx0302",
            ("23gabonx0402", "L"): "16afrisr0602",
            ("23gabonx0402", "P"): "16afrisr0602",
            ("23gabonx0403", "L"): "16afrisr0602",
            ("23gabonx0403", "P"): "16afrisr0602",
            ("23gabonx0404", "L"): "16afrisr0602",
            ("23gabonx0404", "P"): "16afrisr0602",
            ("23gabonx0405", "L"): "16afrisr0602",
            ("23gabonx0405", "P"): "16afrisr0602",
            ("23gabonx0406", "L"): "16afrisr0602",
            ("23gabonx0406", "P"): "16afrisr0602",
            ("23gabonx0407", "L"): "16afrisr0602",
            ("23gabonx0407", "P"): "16afrisr0602",
            ("23gabonx0408", "L"): "16afrisr0602",
            ("23gabonx0408", "P"): "16afrisr0602",
            ("23gabonx0409", "L"): "16afrisr0602",
            ("23gabonx0409", "P"): "16afrisr0602",
            ("23gabonx0410", "L"): "16afrisr0602",
            ("23gabonx0410", "P"): "16afrisr0602",
            ("23gabonx0411", "L"): "16afrisr0602",
            ("23gabonx0411", "P"): "16afrisr0602",
            ("23gabonx0412", "L"): "16afrisr0602",
            ("23gabonx0412", "P"): "16afrisr0602",
            ("23gabonx0413", "L"): "16afrisr0602",
            ("23gabonx0413", "P"): "16afrisr0602",
            ("23gabonx0414", "L"): "16afrisr0602",
            ("23gabonx0414", "P"): "16afrisr0602",
            ("23gabonx0504", "L"): "16afrisr0502",
            ("23gabonx0504", "P"): "16afrisr0502",
            ("23gabonx0505", "L"): "16afrisr0502",
            ("23gabonx0505", "P"): "16afrisr0502",
            ("23gabonx0506", "L"): "16afrisr0502",
            ("23gabonx0506", "P"): "16afrisr0502",
            ("23gabonx0507", "L"): "16afrisr0502",
            ("23gabonx0507", "P"): "16afrisr0502",
            ("23gabonx0508", "L"): "16afrisr0502",
            ("23gabonx0508", "P"): "16afrisr0502",
            ("23gabonx0509", "L"): "16afrisr0502",
            ("23gabonx0509", "P"): "16afrisr0502",
            ("23gabonx0510", "L"): "16afrisr0502",
            ("23gabonx0510", "P"): "16afrisr0502",
            ("23gabonx0511", "L"): "16afrisr0502",
            ("23gabonx0511", "P"): "16afrisr0502",
            ("23gabonx0512", "L"): "16afrisr0502",
            ("23gabonx0512", "P"): "16afrisr0502",
            ("23gabonx0513", "L"): "16afrisr0502",
            ("23gabonx0513", "P"): "16afrisr0502",
            ("23gabonx0514", "L"): "16afrisr0502",
            ("23gabonx0514", "P"): "16afrisr0502",
            ("23gabonx0515", "L"): "16afrisr0502",
            ("23gabonx0515", "P"): "16afrisr0502",
            ("23gabonx0602", "L"): "16afrisr1206",
            ("23gabonx0602", "P"): "16afrisr1206",
            ("23gabonx0603", "L"): "16afrisr1206",
            ("23gabonx0603", "P"): "16afrisr1206",
            ("23gabonx0604", "L"): "16afrisr1206",
            ("23gabonx0604", "P"): "16afrisr1206",
            ("23gabonx0605", "L"): "16afrisr1206",
            ("23gabonx0605", "P"): "16afrisr1206",
            ("23gabonx0606", "L"): "16afrisr1206",
            ("23gabonx0606", "P"): "16afrisr1206",
            ("23gabonx0607", "L"): "16afrisr1206",
            ("23gabonx0607", "P"): "16afrisr1206",
            ("23gabonx0609", "L"): "16afrisr1206",
            ("23gabonx0609", "P"): "16afrisr1206",
            ("23gabonx0610", "L"): "16afrisr1206",
            ("23gabonx0610", "P"): "16afrisr1206",
            ("23gabonx0611", "L"): "16afrisr1206",
            ("23gabonx0611", "P"): "16afrisr1206",
            ("23gabonx0612", "L"): "16afrisr1206",
            ("23gabonx0612", "P"): "16afrisr1206",
            ("23gabonx0702", "L"): None,
            ("23gabonx0702", "P"): None,
            ("23gabonx0703", "L"): "23gabonx0702",
            ("23gabonx0703", "P"): "23gabonx0702",
            ("23gabonx0704", "L"): "23gabonx0702",
            ("23gabonx0704", "P"): "23gabonx0702",
            ("23gabonx0705", "L"): "23gabonx0702",
            ("23gabonx0705", "P"): "23gabonx0702",
            ("23gabonx0706", "L"): "23gabonx0702",
            ("23gabonx0706", "P"): "23gabonx0702",
            ("23gabonx0707", "L"): "23gabonx0702",
            ("23gabonx0707", "P"): "23gabonx0702",
            ("23gabonx0708", "L"): "23gabonx0702",
            ("23gabonx0708", "P"): "23gabonx0702",
            ("23gabonx0709", "L"): "23gabonx0702",
            ("23gabonx0709", "P"): "23gabonx0702",
            ("23gabonx0710", "L"): "23gabonx0702",
            ("23gabonx0710", "P"): "23gabonx0702",
            ("23gabonx0711", "L"): "23gabonx0702",
            ("23gabonx0711", "P"): "23gabonx0702",
            ("23gabonx0712", "L"): "23gabonx0702",
            ("23gabonx0712", "P"): "23gabonx0702",
            ("23gabonx0713", "L"): "23gabonx0702",
            ("23gabonx0713", "P"): "23gabonx0702",
            ("23gabonx0802", "L"): "16afrisr0702",
            ("23gabonx0802", "P"): "16afrisr0702",
            ("23gabonx0803", "L"): "16afrisr0702",
            ("23gabonx0803", "P"): "16afrisr0702",
            ("23gabonx0804", "L"): "16afrisr0702",
            ("23gabonx0804", "P"): "16afrisr0702",
            ("23gabonx0805", "L"): "16afrisr0702",
            ("23gabonx0805", "P"): "16afrisr0702",
            ("23gabonx0806", "L"): "16afrisr0702",
            ("23gabonx0806", "P"): "16afrisr0702",
            ("23gabonx0807", "L"): "16afrisr0702",
            ("23gabonx0807", "P"): "16afrisr0702",
            ("23gabonx0808", "L"): "16afrisr0702",
            ("23gabonx0808", "P"): "16afrisr0702",
            ("23gabonx0809", "L"): "16afrisr0702",
            ("23gabonx0809", "P"): "16afrisr0702",
            ("23gabonx0810", "L"): "16afrisr0702",
            ("23gabonx0810", "P"): "16afrisr0702",
            ("23gabonx0811", "L"): "16afrisr0702",
            ("23gabonx0811", "P"): "16afrisr0702",
            ("23gabonx0812", "L"): "16afrisr0702",
            ("23gabonx0812", "P"): "16afrisr0702",
            ("23gabonx0813", "L"): "16afrisr0702",
            ("23gabonx0813", "P"): "16afrisr0702",
            ("23gabonx0902", "L"): "16afrisr0602",
            ("23gabonx0902", "P"): "16afrisr0602",
            ("23gabonx0903", "L"): None,
            ("23gabonx0903", "P"): None,
            ("23gabonx0904", "L"): "16afrisr0903",
            ("23gabonx0904", "P"): "16afrisr0903",
            ("23gabonx0905", "L"): "16afrisr0602",
            ("23gabonx0905", "P"): "16afrisr0602",
            ("23gabonx0906", "L"): "23gabonx0903",
            ("23gabonx0906", "P"): "23gabonx0903",
            ("23gabonx0907", "L"): "16afrisr0903",
            ("23gabonx0907", "P"): "16afrisr0903",
            ("23gabonx0908", "L"): "16afrisr0602",
            ("23gabonx0908", "P"): "16afrisr0602",
            ("23gabonx0909", "L"): "23gabonx0903",
            ("23gabonx0909", "P"): "23gabonx0903",
            ("23gabonx0910", "L"): "16afrisr0903",
            ("23gabonx0910", "P"): "16afrisr0903",
            ("23gabonx0911", "L"): "16afrisr0602",
            ("23gabonx0911", "P"): "16afrisr0602",
            ("23gabonx0912", "L"): "23gabonx0903",
            ("23gabonx0912", "P"): "23gabonx0903",
            ("23gabonx0913", "L"): "16afrisr0903",
            ("23gabonx0913", "P"): "16afrisr0903",
            ("23gabonx0914", "L"): "16afrisr0602",
            ("23gabonx0914", "P"): "16afrisr0602",
            ("23gabonx0915", "L"): "23gabonx0903",
            ("23gabonx0915", "P"): "23gabonx0903",
            ("23gabonx0916", "L"): "16afrisr0903",
            ("23gabonx0916", "P"): "16afrisr0903",
            ("23gabonx0917", "L"): "16afrisr0602",
            ("23gabonx0917", "P"): "16afrisr0602",
            ("23gabonx0918", "L"): "23gabonx0903",
            ("23gabonx0918", "P"): "23gabonx0903",
            ("23gabonx1002", "L"): "16afrisr0502",
            ("23gabonx1002", "P"): "16afrisr0502",
            ("23gabonx1003", "L"): "16afrisr0502",
            ("23gabonx1003", "P"): "16afrisr0502",
            ("23gabonx1004", "L"): "16afrisr0502",
            ("23gabonx1004", "P"): "16afrisr0502",
            ("23gabonx1005", "L"): "16afrisr0502",
            ("23gabonx1005", "P"): "16afrisr0502",
            ("23gabonx1006", "L"): "16afrisr0502",
            ("23gabonx1006", "P"): "16afrisr0502",
            ("23gabonx1007", "L"): "16afrisr0502",
            ("23gabonx1007", "P"): "16afrisr0502",
            ("23gabonx1104", "L"): "16afrisr0502",
            ("23gabonx1104", "P"): "16afrisr0502",
            ("23gabonx1105", "L"): "16afrisr0502",
            ("23gabonx1105", "P"): "16afrisr0502",
            ("23gabonx1106", "L"): "16afrisr0502",
            ("23gabonx1106", "P"): "16afrisr0502",
            ("23gabonx1107", "L"): "16afrisr0502",
            ("23gabonx1107", "P"): "16afrisr0502",
            ("23gabonx1108", "L"): "16afrisr0502",
            ("23gabonx1108", "P"): "16afrisr0502",
            ("23gabonx1202", "L"): "16afrisr1206",
            ("23gabonx1202", "P"): "16afrisr1206",
            ("23gabonx1203", "L"): "16afrisr1206",
            ("23gabonx1203", "P"): "16afrisr1206",
            ("23gabonx1204", "L"): "16afrisr1206",
            ("23gabonx1204", "P"): "16afrisr1206",
            ("23gabonx1206", "L"): "16afrisr1206",
            ("23gabonx1206", "P"): "16afrisr1206",
            ("23gabonx1207", "L"): "16afrisr1206",
            ("23gabonx1207", "P"): "16afrisr1206",
            ("23gabonx1208", "L"): "16afrisr1206",
            ("23gabonx1208", "P"): "16afrisr1206",
            ("23gabonx1209", "L"): "16afrisr1206",
            ("23gabonx1209", "P"): "16afrisr1206",
            ("23gabonx1210", "L"): "16afrisr1206",
            ("23gabonx1210", "P"): "16afrisr1206",
            ("23gabonx1211", "L"): "16afrisr1206",
            ("23gabonx1211", "P"): "16afrisr1206",
            ("23gabonx1212", "L"): "16afrisr1206",
            ("23gabonx1212", "P"): "16afrisr1206",
            ("23gabonx1213", "L"): "16afrisr1206",
            ("23gabonx1213", "P"): "16afrisr1206",
            ("23gabonx1402", "L"): None,
            ("23gabonx1402", "P"): None,
            ("23gabonx1403", "L"): "23gabonx1402",
            ("23gabonx1403", "P"): "23gabonx1402",
            ("23gabonx1404", "L"): "23gabonx1402",
            ("23gabonx1404", "P"): "23gabonx1402",
            ("23gabonx1405", "L"): "23gabonx1402",
            ("23gabonx1405", "P"): "23gabonx1402",
            ("23gabonx1406", "L"): "23gabonx1402",
            ("23gabonx1406", "P"): "23gabonx1402",
            ("23gabonx1407", "L"): "23gabonx1402",
            ("23gabonx1407", "P"): "23gabonx1402",
            ("23gabonx1408", "L"): "23gabonx1402",
            ("23gabonx1408", "P"): "23gabonx1402",
            ("23gabonx1409", "L"): "23gabonx1402",
            ("23gabonx1409", "P"): "23gabonx1402",
            ("23gabonx1410", "L"): "23gabonx1402",
            ("23gabonx1410", "P"): "23gabonx1402",
            ("23gabonx1411", "L"): "23gabonx1402",
            ("23gabonx1411", "P"): "23gabonx1402",
            ("23gabonx1412", "L"): "23gabonx1402",
            ("23gabonx1412", "P"): "23gabonx1402",
            ("23gabonx1413", "L"): "23gabonx1402",
            ("23gabonx1413", "P"): "23gabonx1402",
            ("23gabonx1602", "L"): "16afrisr0502",
            ("23gabonx1602", "P"): "16afrisr0502",
            ("23gabonx1603", "L"): "16afrisr0502",
            ("23gabonx1603", "P"): "16afrisr0502",
            ("23gabonx1604", "L"): "16afrisr0502",
            ("23gabonx1604", "P"): "16afrisr0502",
            ("23gabonx1605", "L"): "16afrisr0502",
            ("23gabonx1605", "P"): "16afrisr0502",
            ("23gabonx1606", "L"): "16afrisr0502",
            ("23gabonx1606", "P"): "16afrisr0502",
            ("23gabonx1607", "L"): "16afrisr0502",
            ("23gabonx1607", "P"): "16afrisr0502",
            ("23gabonx1608", "L"): "16afrisr0502",
            ("23gabonx1608", "P"): "16afrisr0502",
            ("23gabonx1609", "L"): "16afrisr0502",
            ("23gabonx1609", "P"): "16afrisr0502",
            ("23gabonx1610", "L"): "16afrisr0502",
            ("23gabonx1610", "P"): "16afrisr0502",
            ("23gabonx1611", "L"): "16afrisr0502",
            ("23gabonx1611", "P"): "16afrisr0502",
        }

    def get_pass(self, pass_name, band):
        master_name = self._pass_band_to_master.get((pass_name, band), None)
        return GABONX23Pass(self.campaign_folder, pass_name, band, master_name)

    def get_all_pass_names(self, band):
        pass_names = [pass_name for pass_name, ps_b in self._pass_band_to_master.keys() if ps_b == band]
        return sorted(list(set(pass_names)))  # sort and de-duplicate


class GABONX23Pass:
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
        return fc.mrrat(self._get_rgi_folder() / "RGI-SR" / f"slc_{self.pass_name}_{self.band}{pol}_t{self.band}01.rat")

    def load_rgi_incidence(self, pol=None):
        """
        Load incidence angle from the RGI folder.
        Polarization is ignored for the GABONX 2023 campaign.
        """
        return fc.mrrat(
            self._get_rgi_folder() / "RGI-SR" / f"incidence_{self.pass_name}_{self.band}_t{self.band}01.rat"
        )

    def load_rgi_params(self, pol="hh"):
        """
        Load radar parameters from the RGI folder. Default polarization is "hh".
        """
        return campaign_utils.parse_xml_parameters(
            self._get_rgi_folder() / "RGI-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_t{self.band}01.xml"
        )

    # INF folder

    def load_inf_slc(self, pol):
        """
        Load coregistered SLC in specified polarization ("hh", "hv", "vh", "vv") from the INF folder.
        """
        return fc.mrrat(
            self._get_inf_folder()
            / "INF-SR"
            / f"slc_coreg_{self.master_name}_{self.pass_name}_{self.band}{pol}_t{self.band}01.rat"
        )

    def load_inf_pha_dem(self, pol=None):
        """
        Load interferometric phase correction derived from track and terrain geometry.
        The residual can be used to correct the phase of the coregistered SLCs: coreg_slc * np.exp(1j * phase)
        This is equivalent of subtracting the phase from the interferogram.
        Polarization is ignored for the GABONX 23 campaign.
        """
        return fc.mrrat(
            self._get_inf_folder()
            / "INF-SR"
            / f"pha_dem_{self.master_name}_{self.pass_name}_{self.band}_t{self.band}01.rat"
        )

    def load_inf_pha_fe(self, pol=None):
        """
        Load interferometric flat-Earth phase.
        For the GABONX 23 campaign, this phase is included into pha_dem and pha_fe is 0.
        Polarization is ignored for the GABONX 23 campaign.
        """
        return fc.mrrat(
            self._get_inf_folder()
            / "INF-SR"
            / f"pha_fe_{self.master_name}_{self.pass_name}_{self.band}_t{self.band}01.rat"
        )

    def load_inf_kz(self, pol):
        """
        Load interferometric kz.
        """
        return fc.mrrat(
            self._get_inf_folder()
            / "INF-SR"
            / f"kz_{self.master_name}_{self.pass_name}_{self.band}{pol}_t{self.band}01.rat"
        )

    def load_inf_params(self, pol="hh"):
        """
        Load radar parameters from the INF folder. Default polarization is "hh".
        """
        return campaign_utils.parse_xml_parameters(
            self._get_inf_folder() / "INF-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_t{self.band}01.xml"
        )

    def load_inf_insar_params(self, pol="hh"):
        """
        Load insar radar parameters from the INF folder. Default polarization is "hh".
        """
        return campaign_utils.parse_xml_parameters(
            self._get_inf_folder()
            / "INF-RDP"
            / f"ppinsar_{self.master_name}_{self.pass_name}_{self.band}{pol}_t{self.band}01.xml"
        )

    # GTC folder

    def load_gtc_sr2geo_lut(self):
        lut_az_path = self._get_gtc_folder() / "GTC-LUT" / f"sr2geo_az_{self.pass_name}_{self.band}_t{self.band}01.rat"
        lut_rg_path = self._get_gtc_folder() / "GTC-LUT" / f"sr2geo_rg_{self.pass_name}_{self.band}_t{self.band}01.rat"
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
        gtc_lut = self._get_gtc_folder() / "GTC-LUT"
        lut_az_path = gtc_lut / f"sr2latlon_az_{self.pass_name}_{self.band}_t{self.band}01.rat"
        lut_rg_path = gtc_lut / f"sr2latlon_rg_{self.pass_name}_{self.band}_t{self.band}01.rat"
        hdr_az_path = gtc_lut / f"sr2latlon_az_{self.pass_name}_{self.band}_t{self.band}01.rat.hdr"
        # read lookup tables
        f_az = fc.RatFile(lut_az_path)
        f_rg = fc.RatFile(lut_rg_path)
        header = self._read_sr2latlon_header(hdr_az_path)
        # reading with memory map: fast and read-only
        lut_az = np.flipud(f_az.mread())  # flip image updown, to be consistent with sr2geo
        lut_rg = np.flipud(f_rg.mread())
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

    def _get_rgi_folder(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/T{self.band}01/RGI"

    def _get_inf_folder(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/T{self.band}01/INF"

    def _get_gtc_folder(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/T{self.band}01/GTC"
