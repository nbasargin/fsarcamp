import pathlib
import fsarcamp as fc
from fsarcamp import campaign_utils


class HTERRA22Campaign:
    def __init__(self, campaign_folder):
        """
        Data loader for SAR data for the HTERRA 2022 campaign.
        The `campaign_folder` path on the DLR-HR server as of November 2024:
        "/data/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/01_projects/22HTERRA"        
        """
        self.name = "HTERRA 2022"
        self.campaign_folder = pathlib.Path(campaign_folder)
        self.coreg_to_master = campaign_utils.get_coreg_to_master_mapping(self._pass_hierarchy())

    def get_pass(self, pass_name, band):
        master_name = self.coreg_to_master.get(pass_name, None)
        return HTERRA22Pass(self.campaign_folder, pass_name, band, master_name)

    def _pass_hierarchy(self):
        """Nested dictionary: band -> master passes -> coregistered passes"""
        cl_passes = {
            "22hterra0104": (
                # standard PolInSAR coregistered passes (same flight)
                "22hterra0102",
                "22hterra0103",
                "22hterra0115",
                # additional coregistered passes (between different flights)
                "22hterra0204",
                "22hterra0304",
                "22hterra0404",
                "22hterra0504",
                "22hterra0604",
                "22hterra0704",
                "22hterra0804",
            ),
            "22hterra0204": ("22hterra0202", "22hterra0203", "22hterra0215", "22hterra0216", "22hterra0217"),
            "22hterra0304": ("22hterra0302", "22hterra0303", "22hterra0315"),
            "22hterra0404": ("22hterra0405", "22hterra0406", "22hterra0408"),
            "22hterra0504": ("22hterra0502", "22hterra0503", "22hterra0515"),
            "22hterra0604": ("22hterra0602", "22hterra0603", "22hterra0616", "22hterra0617", "22hterra0618"),
            "22hterra0704": ("22hterra0702", "22hterra0703", "22hterra0717", "22hterra0718"),
            "22hterra0804": ("22hterra0802", "22hterra0803", "22hterra0807", "22hterra0808", "22hterra0809"),
        }
        return {
            "C": cl_passes,
            "L": cl_passes,  # a few more available for L band but not included here
        }


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
        return fc.Geo2SlantRange(fname_lut_az, fname_lut_rg)

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
