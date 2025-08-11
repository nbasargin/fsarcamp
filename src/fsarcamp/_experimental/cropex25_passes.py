"""
Temporary scripts for fsar data
"""

import pathlib
import re


def _match_master_coreg_names(slc_coreg_name: str):
    match = re.search(r"^slc_coreg_(25cropex\d+)_(25cropex\d+).*rat$", slc_coreg_name)
    if match:
        master = match.group(1)
        coreg = match.group(2)
        return master, coreg
    return None, None


def create_pass_band_to_master_mapping():
    path = pathlib.Path("/hrdss/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/25CROPEX/")
    pass_dict = dict()  # (pass_name, band) -> master_name | None
    # for each flight
    for flight_folder in path.iterdir():
        if not flight_folder.is_dir() or not re.match(r"FL\d\d", flight_folder.name):
            continue
        flight_number = int(flight_folder.name[2:4])
        # for each pass
        for pass_folder in flight_folder.iterdir():
            if not pass_folder.is_dir() or not re.match(r"PS\d\d", pass_folder.name):
                continue
            pass_number = int(pass_folder.name[2:4])
            # for each band
            for band in ["X", "C", "S", "L"]:
                band_folder = pass_folder / f"T01{band}"
                if not band_folder.exists() or not band_folder.is_dir():
                    continue
                masters = set()
                pass_name = f"25cropex{flight_number:02}{pass_number:02}"
                for subfolder in band_folder.iterdir():
                    inf_sr = subfolder / "INF-SR"
                    if subfolder.is_dir() and re.match("INF*", subfolder.name) and inf_sr.exists():
                        for infsr in inf_sr.iterdir():
                            master, coreg = _match_master_coreg_names(infsr.name)
                            if master is not None:
                                masters.add(master)
                            if coreg is not None and coreg != pass_name:
                                print(f"!! warning, coregistered pass name mismatch {pass_name} {coreg}")
                if (pass_name, band) in pass_dict:
                    print(f"!! warning, re-definition of {pass_name} {band}")
                if len(masters) > 1:
                    print(f"!! warning, multiple masters for {pass_name} {band}")
                master_name = None if len(masters) == 0 else list(masters)[0]
                pass_dict[pass_name, band] = master_name
    # sort and print hierarchy
    pass_dict = dict(sorted(pass_dict.items()))
    print(pass_dict)


if __name__ == "__main__":
    create_pass_band_to_master_mapping()
