"""
sphere.py

Generates random points either filling a sphere's volume uniformly, or
lying on its surface, depending on 'surface_only'.
"""

import numpy as np
from .base import ShapeGenerator


class SphereGenerator(ShapeGenerator):
    def __init__(self, radius=1.0, surface_only=False, **kwargs):
        super().__init__(**kwargs)
        self.radius = float(radius)
        self.surface_only = bool(surface_only)

    def generate(self) -> np.ndarray:
        directions = self.rng.normal(size=(self.num_points, 3))
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)

        if self.surface_only:
            radii = np.full((self.num_points, 1), self.radius, dtype=np.float32)
        else:
            u = self.rng.uniform(0.0, 1.0, size=(self.num_points, 1))
            radii = self.radius * np.cbrt(u)

        points = directions * radii
        points += self.center
        return points.astype(np.float32)
