"""
motion/orbit.py
"""

import numpy as np
from .base import Motion

class OrbitMotion(Motion):
    """Circular motion around the shape's base_center, in the plane
    perpendicular to 'axis'."""

    def __init__(self, orbit_radius=1.0, angular_speed=1.0, axis='z'):
        self.orbit_radius = float(orbit_radius)
        self.angular_speed = float(angular_speed)
        self.axis = axis.lower()

        if self.axis not in ('x', 'y', 'z'):
            raise ValueError(f"Invalid orbit axis '{axis}'. Use 'x', 'y', or 'z'.")

    def offset(self, t: float) -> np.ndarray:
        angle = self.angular_speed * t
        a = self.orbit_radius * np.cos(angle)
        b = self.orbit_radius * np.sin(angle)

        if self.axis == 'z':
            return np.array([a, b, 0.0], dtype=np.float32)
        elif self.axis == 'y':
            return np.array([a, 0.0, b], dtype=np.float32)
        else:  # axis == 'x'
            return np.array([0.0, a, b], dtype=np.float32)