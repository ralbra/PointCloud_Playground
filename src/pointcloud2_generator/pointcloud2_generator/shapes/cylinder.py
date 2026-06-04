import numpy as np
from .base import ShapeGenerator

class CylinderGenerator(ShapeGenerator):
    def __init__(self, radius=1.0, height=2.0, **kwargs):
        super().__init__(**kwargs)
        self.radius = float(radius)
        self.height = float(height)

    def generate(self):
        theta = self.rng.uniform(0.0, 2.0 * np.pi, self.num_points)
        r = self.radius * np.sqrt(self.rng.uniform(0.0, 1.0, self.num_points))
        z = self.rng.uniform(-self.height / 2.0, self.height / 2.0, self.num_points)

        x = r * np.cos(theta)
        y = r * np.sin(theta)

        points = np.column_stack((x, y, z))
        points += self.center
        return points.astype(np.float32)