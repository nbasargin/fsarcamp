def get_hterra22_pauli_rgb_max(band):
    """Get the max cutoff values for the Pauli RGB images, for each channel (R, G, B)."""
    return {"C": (0.55, 0.48, 0.95), "L": (0.30, 0.20, 0.49)}[band]
