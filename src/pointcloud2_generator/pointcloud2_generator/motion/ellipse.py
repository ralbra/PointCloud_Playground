"""
motion/ellipse.py
"""

import numpy as np
from .base import Motion

class EllipseMotion(Motion):
    """Elliptical motion around the shape's base_center, in the plane
    perpendicular to 'axis'. radius_a and radius_b are the two semi-axes."""

    def __init__(self, radius_a=1.0, radius_b=0.5, angular_speed=1.0, axis='z'):
        self.radius_a = float(radius_a)
        self.radius_b = float(radius_b)
        self.angular_speed = float(angular_speed)
        self.axis = axis.lower()

        if self.axis not in ('x', 'y', 'z'):
            raise ValueError(f"Invalid ellipse axis '{axis}'. Use 'x', 'y', or 'z'.")

    def offset(self, t: float) -> np.ndarray:
        angle = self.angular_speed * t
        a = self.radius_a * np.cos(angle)
        b = self.radius_b * np.sin(angle)

        if self.axis == 'z':
            return np.array([a, b, 0.0], dtype=np.float32)
        elif self.axis == 'y':
            return np.array([a, 0.0, b], dtype=np.float32)
        else:  # axis == 'x'
            return np.array([0.0, a, b], dtype=np.float32)
