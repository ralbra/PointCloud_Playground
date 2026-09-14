"""
motion.py

Optional time-based motion for shapes. A Motion object computes an xyz
offset for a given elapsed time; ShapeGenerator adds that offset to the
shape's base_center to get its current, animated center.
"""

from abc import ABC, abstractmethod
import numpy as np


class Motion(ABC):
    @abstractmethod
    def offset(self, t: float) -> np.ndarray:
        """Returns an xyz offset (3,) float32 array for elapsed time t (seconds)."""
        pass


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


class LinearMotion(Motion):
    """Constant-velocity motion along a fixed direction vector."""

    def __init__(self, velocity=(0.0, 0.0, 0.0)):
        self.velocity = np.array(velocity, dtype=np.float32)

    def offset(self, t: float) -> np.ndarray:
        return self.velocity * t