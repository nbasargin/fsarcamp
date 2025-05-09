import pathlib
import fsarcamp as fc
from fsarcamp import campaign_utils


class CROPEX14Campaign:
    def __init__(self, campaign_folder):
        """        
        Data loader for SAR data for the CROPEX 2014 campaign.
        The `campaign_folder` path on the DLR-HR server as of November 2024:
        "/data/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/CROPEX/CROPEX14"
        """
        self.name = "CROPEX 2014"
        self.campaign_folder = pathlib.Path(campaign_folder)
        self.coreg_to_master = campaign_utils.get_coreg_to_master_mapping(self._pass_hierarchy())

    def get_pass(self, pass_name, band):
        master_name = self.coreg_to_master.get(pass_name, None)
        return CROPEX14Pass(self.campaign_folder, pass_name, band, master_name)

    def _pass_hierarchy(self):
        """Nested dictionary: band -> master passes -> coregistered passes"""
        x_passes = {
            "14cropex0102": ("14cropex0103", "14cropex0105", "14cropex0106"),
            "14cropex0203": ("14cropex0202", "14cropex0204", "14cropex0206"),
            "14cropex0316": (
                "14cropex0311",
                "14cropex0312",
                "14cropex0313",
                "14cropex0314",
                "14cropex0315",
                "14cropex0317",
                "14cropex0318",
                "14cropex0319",
                "14cropex0321",
            ),
            "14cropex0402": ("14cropex0403", "14cropex0404"),
            "14cropex0504": ("14cropex0502", "14cropex0505"),
            "14cropex0610": (
                "14cropex0604",
                "14cropex0605",
                "14cropex0606",
                "14cropex0607",
                "14cropex0608",
                "14cropex0609",
                "14cropex0611",
                "14cropex0612",
                "14cropex0615",
            ),
            "14cropex0708": (
                "14cropex0702",
                "14cropex0704",
                "14cropex0705",
                "14cropex0706",
                "14cropex0707",
                "14cropex0709",
                "14cropex0710",
                "14cropex0711",
                "14cropex0712",
            ),
            "14cropex0804": ("14cropex0802", "14cropex0806"),
            "14cropex0805": (),  # empty inf folder
            "14cropex0904": (
                "14cropex0902",
                "14cropex0905",
                "14cropex0906",
                "14cropex0907",
                "14cropex0908",
                "14cropex0909",
                "14cropex0910",
                "14cropex0911",
                "14cropex0912",
            ),
            "14cropex1003": ("14cropex1002", "14cropex1004", "14cropex1006"),
            "14cropex1104": (
                "14cropex1102",
                "14cropex1105",
                "14cropex1106",
                "14cropex1107",
                "14cropex1108",
                "14cropex1109",
                "14cropex1110",
                "14cropex1111",
                "14cropex1112",
            ),
            "14cropex1203": ("14cropex1204", "14cropex1205", "14cropex1206", "14cropex1208", "14cropex1210"),
            "14cropex1307": (
                "14cropex1305",
                "14cropex1308",
                "14cropex1309",
                "14cropex1310",
                "14cropex1312",
                "14cropex1313",
                "14cropex1314",
                "14cropex1315",
                "14cropex1316",
            ),
            "14cropex1402": ("14cropex1403", "14cropex1405"),
            "14cropex1502": (),  # empty inf folder
            "14cropex1503": ("14cropex1505", "14cropex1507", "14cropex1509", "14cropex1511", "14cropex1513"),
            "14cropex1504": ("14cropex1506", "14cropex1508", "14cropex1510", "14cropex1512"),
        }
        # C band passes mostly equivalent to X band, but a few are missing or have issues in the RGI folder
        c_passes = {
            "14cropex0102": ("14cropex0103", "14cropex0106"),  # missing "14cropex0105"
            "14cropex0203": ("14cropex0202", "14cropex0204"),  # missing "14cropex0206"
            "14cropex0316": (
                "14cropex0311",
                "14cropex0312",
                "14cropex0313",
                "14cropex0314",
                "14cropex0315",
                "14cropex0317",
                "14cropex0318",
                "14cropex0319",
            ),  # missing "14cropex0321"
            "14cropex0402": ("14cropex0403",),  # missing "14cropex0404"
            "14cropex0504": ("14cropex0505",),  # missing "14cropex0502"
            "14cropex0610": (
                "14cropex0604",
                "14cropex0605",
                "14cropex0606",
                "14cropex0607",
                "14cropex0608",
                "14cropex0609",
                "14cropex0611",
                "14cropex0612",
            ),  # missing "14cropex0615"
            "14cropex0708": (
                "14cropex0704",
                "14cropex0705",
                "14cropex0706",
                "14cropex0707",
                "14cropex0709",
                "14cropex0710",
                "14cropex0711",
                "14cropex0712",
            ),  # missing "14cropex0702"
            "14cropex0804": ("14cropex0806",),  # missing "14cropex0802"
            "14cropex0805": (),  # empty inf folder
            "14cropex0904": (
                "14cropex0905",
                "14cropex0906",
                "14cropex0907",
                "14cropex0908",
                "14cropex0909",
                "14cropex0910",
                "14cropex0911",
                "14cropex0912",
            ),  # missing "14cropex0902"
            "14cropex1003": ("14cropex1002", "14cropex1004"),  # missing "14cropex1006"
            "14cropex1104": (
                "14cropex1105",
                "14cropex1107",
                "14cropex1108",
                "14cropex1109",
                "14cropex1110",
                "14cropex1111",
                "14cropex1112",
            ),  # missing "14cropex1102", RGI issues in "14cropex1106"
            "14cropex1203": (
                "14cropex1204",
                "14cropex1205",
                "14cropex1206",
            ),  # missing "14cropex1208" and "14cropex1210"
            "14cropex1307": (
                "14cropex1308",
                "14cropex1309",
                "14cropex1310",
                "14cropex1312",
                "14cropex1313",
                "14cropex1314",
                "14cropex1315",
                "14cropex1316",
            ),  # missing "14cropex1305"
            "14cropex1402": ("14cropex1403",),  # missing "14cropex1405"
            "14cropex1502": (),  # empty inf folder
            "14cropex1503": (
                "14cropex1505",
                "14cropex1507",
                "14cropex1511",
                "14cropex1513",
            ),  # RGI issues in "14cropex1509"
            "14cropex1504": ("14cropex1506", "14cropex1508", "14cropex1510", "14cropex1512"),
        }
        l_passes = {
            "14cropex0210": ("14cropex0209", "14cropex0211"),
            "14cropex0305": (
                "14cropex0302",
                "14cropex0303",
                "14cropex0304",
                "14cropex0306",
                "14cropex0307",
                "14cropex0308",
                "14cropex0309",
            ),
            "14cropex0620": ("14cropex0618", "14cropex0619", "14cropex0621", "14cropex0622", "14cropex0623"),
            "14cropex0718": (
                "14cropex0714",
                "14cropex0715",
                "14cropex0716",
                "14cropex0717",
                "14cropex0719",
                "14cropex0720",
            ),
            "14cropex0914": (
                "14cropex0915",
                "14cropex0916",
                "14cropex0917",
                "14cropex0918",
                "14cropex0919",
                "14cropex0920",
            ),
            "14cropex1114": (
                "14cropex1115",
                "14cropex1116",
                "14cropex1117",
                "14cropex1118",
                "14cropex1119",
                "14cropex1120",
                "14cropex1121",
            ),
            "14cropex1318": (
                "14cropex1319",
                "14cropex1320",
                "14cropex1321",
                "14cropex1322",
                "14cropex1323",
                "14cropex1324",
            ),
            "14cropex1622": (),  # has a different lookup table
        }
        # band -> master passes -> coregistered passes
        return {"X": x_passes, "C": c_passes, "L": l_passes}


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
        return fc.Geo2SlantRange(fname_lut_az, fname_lut_rg)

    # Helpers

    def _get_pass_try_folder(self):
        """The CROPEX 14 campaign has try folder "T01" for all passes."""
        flight_id, pass_id = campaign_utils.get_flight_and_pass_ids(self.pass_name)
        return self.campaign_folder / f"FL{flight_id}/PS{pass_id}/T01"

    def __repr__(self):
        return f"{self.pass_name}_{self.band}"
