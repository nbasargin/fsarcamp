"""
Temporary scripts for fsar data
"""

import pathlib
import re


def _match_master_coreg_names_by_band(slc_coreg_name: str, band: str):
    match = re.search(f"^slc_coreg_(14cropex\\d+)_(14cropex\\d+)_{band}[hv][hv].*rat$", slc_coreg_name)
    if match:
        master = match.group(1)
        coreg = match.group(2)
        return master, coreg
    return None, None


def create_pass_band_to_master_mapping():
    path = pathlib.Path("/hrdss/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/CROPEX/CROPEX14/")
    pass_dict = dict()  # (pass_name, band) -> set of master names
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
            try_folder = pass_folder / "T01"
            if not try_folder.exists() or not try_folder.is_dir():
                continue
            for band in ["X", "C", "L"]:
                pass_name = f"14cropex{flight_number:02}{pass_number:02}"
                # check whether RGI or INF slc for the given band exist
                rgi_slc_path = try_folder / f"RGI/RGI-SR/slc_{pass_name}_{band}hh_t01.rat"
                if rgi_slc_path.exists():
                    pass_dict[pass_name, band] = set()

                inf_sr_path = try_folder / "INF/INF-SR/"
                if not inf_sr_path.exists() or not inf_sr_path.is_dir():
                    continue # no master name
                
                masters = pass_dict.get((pass_name, band), set())
                for inf_item in inf_sr_path.iterdir():
                    master, coreg = _match_master_coreg_names_by_band(inf_item.name, band)
                    if master is not None:
                        masters.add(master)
                    if coreg is not None and coreg != pass_name:
                        print(f"!! warning, coregistered pass name mismatch {pass_name} {coreg}")
                if len(masters) > 0:
                    pass_dict[pass_name, band] = masters

    # check for double masters etc
    final_dict = dict()
    for (pass_name, band), masters in pass_dict.items():
        if len(masters) > 1:
            print(f"!! warning, multiple masters for {pass_name} {band}: {masters}, setting to None")
            master_name = None
        elif len(masters) == 0:
            master_name = None
        else:
            master_name = list(masters)[0]
        final_dict[pass_name, band] = master_name
    # sort and print hierarchy
    final_dict = dict(sorted(final_dict.items()))
    print(final_dict)


if __name__ == "__main__":
    create_pass_band_to_master_mapping()
