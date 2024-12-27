import platform
import pathlib


def get_polinsar_folder():
    """
    Get the default path to the DLR-HR-RKO Pol-InSAR / InfoRetrieval folder.
    """
    if platform.system() == "Windows":
        return pathlib.Path("//hr-fs/HR_Data/Pol-InSAR_InfoRetrieval/")
    else:
        return pathlib.Path("/data/HR_Data/Pol-InSAR_InfoRetrieval/")
