"""
motion/bob.py
"""

import numpy as np
from .base import Motion

class BobMotion(Motion):
    """Sinusoidal oscillation along a single axis."""

    def __init__(self, amplitude=1.0, frequency=1.0, axis='z'):
        self.amplitude = float(amplitude)
        self.frequency = float(frequency)
        self.axis = axis.lower()

        if self.axis not in ('x', 'y', 'z'):
            raise ValueError(f"Invalid bob axis '{axis}'. Use 'x', 'y', or 'z'.")

    def offset(self, t: float) -> np.ndarray:
        value = self.amplitude * np.sin(2.0 * np.pi * self.frequency * t)
        vec = np.zeros(3, dtype=np.float32)
        idx = {'x': 0, 'y': 1, 'z': 2}[self.axis]
        vec[idx] = value
        return vec