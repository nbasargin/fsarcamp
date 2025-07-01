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


def _insert_into_hierarchy(hierarchy, pass_name, band, master_list):
    if band not in hierarchy:
        hierarchy[band] = dict()
    band_hierarchy = hierarchy[band]
    if len(master_list) == 0:
        # this pass is master pass
        if pass_name not in band_hierarchy:
            band_hierarchy[pass_name] = []
    else:
        for master in master_list:
            if master not in band_hierarchy:
                band_hierarchy[master] = []
            coreg_list = band_hierarchy[master]
            coreg_list.append(pass_name)


def create_pass_hierarchy():
    path = pathlib.Path("/hrdss/HR_Data/Pol-InSAR_InfoRetrieval/01_projects/25CROPEX/")
    pass_hierarchy = {
        "X": dict(),
        "C": dict(),
        "S": dict(),
        "L": dict(),
    }  # band -> master passes -> coregistered passes
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
                relevant_folders = []
                masters = set()
                pass_name = f"25cropex{flight_number:02}{pass_number:02}"
                for subfolder in band_folder.iterdir():
                    if subfolder.is_dir() and re.match("(RGI*)|(INF*)|(GTC*)", subfolder.name):
                        relevant_folders.append(subfolder.name)
                    inf_sr = subfolder / "INF-SR"
                    if subfolder.is_dir() and re.match("INF*", subfolder.name) and inf_sr.exists():
                        for infsr in inf_sr.iterdir():
                            master, coreg = _match_master_coreg_names(infsr.name)
                            if master is not None:
                                masters.add(master)
                            if coreg is not None and coreg != pass_name:
                                print(f"!! warning, coregistered pass name mismatch {pass_name} {coreg}")
                _insert_into_hierarchy(pass_hierarchy, pass_name, band, list(masters))
    # sort and print hierarchy
    print("hierarchy")
    for band, master_coreg_list in pass_hierarchy.items():
        pass_hierarchy[band] = dict(sorted(master_coreg_list.items()))
        for master, coreg_list in pass_hierarchy[band].items():
            pass_hierarchy[band][master] = tuple(sorted(coreg_list))
            print(band, master, pass_hierarchy[band][master])
    print("all together")
    print(pass_hierarchy)


if __name__ == "__main__":
    create_pass_hierarchy()
