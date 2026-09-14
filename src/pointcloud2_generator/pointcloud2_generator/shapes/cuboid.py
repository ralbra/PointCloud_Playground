"""
cuboid.py

Generates random points uniformly filling a cuboid volume of size
size_x x size_y x size_z, centered on 'center'.
"""

import numpy as np
from .base import ShapeGenerator


class CuboidGenerator(ShapeGenerator):
    def __init__(self, size_x=1.0, size_y=1.0, size_z=1.0, **kwargs):
        super().__init__(**kwargs)
        self.size_x = float(size_x)
        self.size_y = float(size_y)
        self.size_z = float(size_z)

    def generate(self) -> np.ndarray:
        x = self.rng.uniform(-self.size_x / 2.0, self.size_x / 2.0, self.num_points)
        y = self.rng.uniform(-self.size_y / 2.0, self.size_y / 2.0, self.num_points)
        z = self.rng.uniform(-self.size_z / 2.0, self.size_z / 2.0, self.num_points)

        points = np.column_stack((x, y, z))
        points += self.center
        return points.astype(np.float32)