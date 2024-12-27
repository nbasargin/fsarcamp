"""
F-SAR parameters and constants.
"""


def get_fsar_center_frequency(band):
    """Get F-SAR center frequency (in Hz) by band."""
    if band == "X":
        return 9.6e9
    if band == "C":
        return 5.3e9
    if band == "S":
        return 3.25e9
    if band == "L":
        return 1.325e9
    if band == "P":
        return 0.35e9
    raise ValueError(f"Unsupported band: {band}")


def get_fsar_wavelength(band):
    """Get F-SAR wavelength (in meters) by band."""
    c = 299792458  # m / s
    return c / get_fsar_center_frequency(band)
