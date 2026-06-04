import numpy as np

class SphereGenerator:
    def __init__(self, radius=1.0, num_points=1000, center=(0.0, 0.0, 0.0), surface_only=False):
        self.radius = float(radius)
        self.num_points = int(num_points)
        self.center = np.array(center, dtype=np.float32)
        self.surface_only = surface_only

    def generate(self):
        directions = np.random.normal(size=(self.num_points, 3))
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)

        if self.surface_only:
            radii = np.full((self.num_points, 1), self.radius, dtype=np.float32)
        else:
            u = np.random.uniform(0.0, 1.0, size=(self.num_points, 1))
            radii = self.radius * np.cbrt(u)

        points = directions * radii
        points += self.center
        return points.astype(np.float32)