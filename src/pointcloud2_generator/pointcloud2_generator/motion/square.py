"""
motion/square.py
"""

import numpy as np
from .base import Motion


class SquareMotion(Motion):
    """Constant-speed motion around the perimeter of a square, in the
    plane perpendicular to 'axis', centered on the shape's base_center."""

    def __init__(self, side_length=1.0, speed=1.0, axis='z'):
        self.side_length = float(side_length)
        self.speed = float(speed)
        self.axis = axis.lower()

        if self.axis not in ('x', 'y', 'z'):
            raise ValueError(f"Invalid square axis '{axis}'. Use 'x', 'y', or 'z'.")

        half = self.side_length / 2.0
        self.corners = np.array([
            (-half, -half),
            (half, -half),
            (half, half),
            (-half, half),
        ], dtype=np.float32)

    def offset(self, t: float) -> np.ndarray:
        perimeter = 4.0 * self.side_length
        if perimeter == 0.0:
            return np.zeros(3, dtype=np.float32)

        dist = (self.speed * t) % perimeter
        segment_index = int(dist // self.side_length)
        local_fraction = (dist % self.side_length) / self.side_length

        p0 = self.corners[segment_index]
        p1 = self.corners[(segment_index + 1) % 4]
        a, b = p0 + (p1 - p0) * local_fraction

        if self.axis == 'z':
            return np.array([a, b, 0.0], dtype=np.float32)
        elif self.axis == 'y':
            return np.array([a, 0.0, b], dtype=np.float32)
        else:  # axis == 'x'
            return np.array([0.0, a, b], dtype=np.float32)