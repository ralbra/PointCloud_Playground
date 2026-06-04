import numpy as np
from .base import ShapeGenerator

class PyramidGenerator(ShapeGenerator):
    def __init__(self, base_size=2.0, height=2.0, **kwargs):
        super().__init__(**kwargs)
        self.base_size = float(base_size)
        self.height = float(height)

    def generate(self):
        u = self.rng.uniform(0.0, 1.0, self.num_points)
        h = self.height * np.cbrt(u)

        half_side = (self.base_size / 2.0) * (h / self.height)
        x = self.rng.uniform(-1.0, 1.0, self.num_points) * half_side
        y = self.rng.uniform(-1.0, 1.0, self.num_points) * half_side
        z = h - self.height / 2.0

        points = np.column_stack((x, y, z))
        points += self.center
        return points.astype(np.float32)