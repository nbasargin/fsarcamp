def get_cropex14_pauli_rgb_max(band):
    """Get the max cutoff values for the Pauli RGB images, for each channel (R, G, B)."""
    return {"X": (0.65, 0.60, 1.22), "C": (0.67, 0.60, 1.13), "L": (0.60, 0.36, 0.87)}[band]
