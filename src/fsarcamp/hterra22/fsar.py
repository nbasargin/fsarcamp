import numpy as np
import pathlib
import rasterio
import rasterio.crs
import rasterio.transform
import fsarcamp as fc
from fsarcamp import campaign_utils


class HTERRA22Campaign:
    def __init__(self, campaign_folder):
        """
        Data loader for SAR data for the HTERRA 2022 campaign.
        The `campaign_folder` path on the DLR-HR server as of August 2025:
        "/hrdss/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/22HTERRA"
        """
        self.name = "HTERRA 2022"
        self.campaign_folder = pathlib.Path(campaign_folder)
        # Mapping for the INF folder: pass_name & band -> master_name
        # Here, the default master_name is used in case there are more than one master.
        self._pass_band_to_master = {
            ("22hterra0102", "C"): "22hterra0104",
            ("22hterra0102", "L"): "22hterra0104",
            ("22hterra0103", "C"): "22hterra0104",
            ("22hterra0103", "L"): "22hterra0104",
            ("22hterra0104", "C"): None,
            ("22hterra0104", "L"): None,
            ("22hterra0115", "C"): "22hterra0104",
            ("22hterra0115", "L"): "22hterra0104",
            ("22hterra0202", "C"): "22hterra0204",
            ("22hterra0202", "L"): "22hterra0204",
            ("22hterra0203", "C"): "22hterra0204",
            ("22hterra0203", "L"): "22hterra0204",
            ("22hterra0204", "C"): "22hterra0104",
            ("22hterra0204", "L"): "22hterra0104",
            ("22hterra0205", "L"): "22hterra0204",
            ("22hterra0206", "L"): "22hterra0204",
            ("22hterra0207", "L"): "22hterra0204",
            ("22hterra0208", "L"): "22hterra0204",
            ("22hterra0209", "L"): "22hterra0204",
            ("22hterra0210", "L"): "22hterra0204",
            ("22hterra0211", "L"): "22hterra0204",
            ("22hterra0212", "L"): "22hterra0204",
            ("22hterra0213", "L"): "22hterra0204",
            ("22hterra0214", "L"): "22hterra0204",
            ("22hterra0215", "C"): "22hterra0204",
            ("22hterra0215", "L"): "22hterra0204",
            ("22hterra0216", "C"): "22hterra0204",
            ("22hterra0216", "L"): "22hterra0204",
            ("22hterra0217", "C"): "22hterra0204",
            ("22hterra0217", "L"): "22hterra0204",
            ("22hterra0302", "C"): "22hterra0304",
            ("22hterra0302", "L"): "22hterra0304",
            ("22hterra0303", "C"): "22hterra0304",
            ("22hterra0303", "L"): "22hterra0304",
            ("22hterra0304", "C"): "22hterra0104",
            ("22hterra0304", "L"): "22hterra0104",
            ("22hterra0315", "C"): "22hterra0304",
            ("22hterra0315", "L"): "22hterra0304",
            ("22hterra0404", "C"): "22hterra0104",
            ("22hterra0404", "L"): "22hterra0104",
            ("22hterra0405", "C"): "22hterra0404",
            ("22hterra0405", "L"): "22hterra0404",
            ("22hterra0406", "C"): "22hterra0404",
            ("22hterra0406", "L"): "22hterra0404",
            ("22hterra0408", "C"): "22hterra0404",
            ("22hterra0408", "L"): "22hterra0404",
            ("22hterra0502", "C"): "22hterra0504",
            ("22hterra0502", "L"): "22hterra0504",
            ("22hterra0503", "C"): "22hterra0504",
            ("22hterra0503", "L"): "22hterra0504",
            ("22hterra0504", "C"): "22hterra0104",
            ("22hterra0504", "L"): "22hterra0104",
            ("22hterra0515", "C"): "22hterra0504",
            ("22hterra0515", "L"): "22hterra0504",
            ("22hterra0602", "C"): "22hterra0604",
            ("22hterra0602", "L"): "22hterra0604",
            ("22hterra0603", "C"): "22hterra0604",
            ("22hterra0603", "L"): "22hterra0604",
            ("22hterra0604", "C"): "22hterra0104",
            ("22hterra0604", "L"): "22hterra0104",
            ("22hterra0616", "C"): "22hterra0604",
            ("22hterra0616", "L"): "22hterra0604",
            ("22hterra0617", "C"): "22hterra0604",
            ("22hterra0617", "L"): "22hterra0604",
            ("22hterra0618", "C"): "22hterra0604",
            ("22hterra0618", "L"): "22hterra0604",
            ("22hterra0702", "C"): "22hterra0704",
            ("22hterra0702", "L"): "22hterra0704",
            ("22hterra0703", "C"): "22hterra0704",
            ("22hterra0703", "L"): "22hterra0704",
            ("22hterra0704", "C"): "22hterra0104",
            ("22hterra0704", "L"): "22hterra0104",
            ("22hterra0716", "L"): "22hterra0704",
            ("22hterra0717", "C"): "22hterra0704",
            ("22hterra0717", "L"): "22hterra0704",
            ("22hterra0718", "C"): "22hterra0704",
            ("22hterra0718", "L"): "22hterra0704",
            ("22hterra0802", "C"): "22hterra0804",
            ("22hterra0802", "L"): "22hterra0804",
            ("22hterra0803", "C"): "22hterra0804",
            ("22hterra0803", "L"): "22hterra0804",
            ("22hterra0804", "C"): "22hterra0104",
            ("22hterra0804", "L"): "22hterra0104",
            ("22hterra0807", "C"): "22hterra0804",
            ("22hterra0807", "L"): "22hterra0804",
            ("22hterra0808", "C"): "22hterra0804",
            ("22hterra0808", "L"): "22hterra0804",
            ("22hterra0809", "C"): "22hterra0804",
            ("22hterra0809", "L"): "22hterra0804",
        }

    def get_pass(self, pass_name, band):
        master_name = self._pass_band_to_master.get((pass_name, band), None)
        return HTERRA22Pass(self.campaign_folder, pass_name, band, master_name)

    def get_all_pass_names(self, band):
        pass_names = [pass_name for pass_name, ps_b in self._pass_band_to_master.keys() if ps_b == band]
        return sorted(list(set(pass_names)))  # sort and de-duplicate

class HTERRA22Pass:
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
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return fc.mrrat(rgi_folder / "RGI-SR" / f"slc_{self.pass_name}_{self.band}{pol}_{try_suffix}.rat")

    def load_rgi_incidence(self, pol=None):
        """
        Load incidence angle from the RGI folder.
        Polarization is ignored for the HTERRA 22 campaign.
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return fc.mrrat(rgi_folder / "RGI-SR" / f"incidence_{self.pass_name}_{self.band}_{try_suffix}.rat")

    def load_rgi_params(self, pol="hh"):
        """
        Load radar parameters from the RGI folder. Default polarization is "hh".
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return campaign_utils.parse_xml_parameters(
            rgi_folder / "RGI-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_{try_suffix}.xml"
        )

    # INF folder

    def load_inf_slc(self, pol):
        """
        Load coregistered SLC in specified polarization ("hh", "hv", "vh", "vv") from the INF folder.
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return fc.mrrat(
            inf_folder / "INF-SR" / f"slc_coreg_{self.master_name}_{self.pass_name}_{self.band}{pol}_{try_suffix}.rat"
        )

    def load_inf_pha_dem(self, pol=None):
        """
        Load interferometric phase correction derived from track and terrain geometry.
        The residual can be used to correct the phase of the coregistered SLCs: coreg_slc * np.exp(1j * phase)
        This is equivalent of subtracting the phase from the interferogram.
        Polarization is ignored for the HTERRA 22 campaign.
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return fc.mrrat(
            inf_folder / "INF-SR" / f"pha_dem_{self.master_name}_{self.pass_name}_{self.band}_{try_suffix}.rat"
        )

    def load_inf_pha_fe(self, pol=None):
        """
        Load interferometric flat-Earth phase.
        For the HTERRA 22 campaign, this phase is included into pha_dem and pha_fe is 0.
        Polarization is ignored for the HTERRA 22 campaign.
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return fc.mrrat(
            inf_folder / "INF-SR" / f"pha_fe_{self.master_name}_{self.pass_name}_{self.band}_{try_suffix}.rat"
        )

    def load_inf_kz(self, pol):
        """
        Load interferometric kz.
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return fc.mrrat(
            inf_folder / "INF-SR" / f"kz_{self.master_name}_{self.pass_name}_{self.band}{pol}_{try_suffix}.rat"
        )

    def load_inf_params(self, pol="hh"):
        """
        Load radar parameters from the INF folder. Default polarization is "hh".
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return campaign_utils.parse_xml_parameters(
            inf_folder / "INF-RDP" / f"pp_{self.pass_name}_{self.band}{pol}_{try_suffix}.xml"
        )

    def load_inf_insar_params(self, pol="hh"):
        """
        Load insar radar parameters from the INF folder. Default polarization is "hh".
        """
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        return campaign_utils.parse_xml_parameters(
            inf_folder / "INF-RDP" / f"ppinsar_{self.master_name}_{self.pass_name}_{self.band}{pol}_{try_suffix}.xml"
        )

    # GTC folder

    def load_gtc_sr2geo_lut(self):
        rgi_folder, inf_folder, gtc_folder, try_suffix = self._get_path_parts()
        fname_lut_az = gtc_folder / "GTC-LUT" / f"sr2geo_az_22hterra0104_{self.band}_{try_suffix}.rat"
        fname_lut_rg = gtc_folder / "GTC-LUT" / f"sr2geo_rg_22hterra0104_{self.band}_{try_suffix}.rat"
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

    def _get_path_parts(self):
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        try_folder_name = {"C": "T01", "L": "T02"}[self.band]
        if self.master_name is not None:
            master_f_id, master_p_id = campaign_utils.get_flight_and_pass_ids(self.master_name)
            inf_folder_name = f"INF_polinsar{flight_id if master_f_id == flight_id else 'All'}{self.band}hh"
        else:
            inf_folder_name = None
        rgi_folder = self.campaign_folder / f"FL{flight_id}/PS{pass_id}/{try_folder_name}/RGI"
        inf_folder = self.campaign_folder / f"FL{flight_id}/PS{pass_id}/{try_folder_name}/{inf_folder_name}"
        # HTERRA 22 has the same coords for all SLCs, only one LUT, valid for all passes
        gtc_folder = self.campaign_folder / f"FL01/PS04/{try_folder_name}/GTC"
        try_suffix = try_folder_name.lower()
        return rgi_folder, inf_folder, gtc_folder, try_suffix

    def __repr__(self):
        return f"{self.pass_name}_{self.band}"
