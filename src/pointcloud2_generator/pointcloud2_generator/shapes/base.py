"""
shapes/base.py

Shared parent class for all shape generators. Handles the arguments every
shape has in common: num_points, center, seed, motion, and the optional
per-shape color/intensity used when the scene's point_type includes an
rgb and/or intensity field (see cloud_format.py).
"""

from abc import ABC, abstractmethod
import numpy as np

from pointcloud2_generator.motion import Motion


class ShapeGenerator(ABC):
    def __init__(
        self,
        num_points=1000,
        center=(0.0, 0.0, 0.0),
        seed=None,
        motion: Motion = None,
        color=None,
        intensity=None,
    ):
        self.num_points = int(num_points)
        self.base_center = np.array(center, dtype=np.float32)
        self.center = self.base_center.copy()
        self.rng = np.random.default_rng(seed)
        self.motion = motion

        # color: optional (r, g, b) tuple, 0-255 each. Only used if the
        # scene's point_type includes an rgb field.
        self.color = tuple(color) if color is not None else None

        # intensity: optional float. Only used if the scene's point_type
        # includes an intensity-like field.
        self.intensity = float(intensity) if intensity is not None else None

    def update_center(self, elapsed_seconds: float):
        """Recomputes self.center for the given elapsed time. Call this
        once per publish tick, before generate()."""
        if self.motion is not None:
            self.center = self.base_center + self.motion.offset(elapsed_seconds)
        else:
            self.center = self.base_center

    @abstractmethod
    def generate(self) -> np.ndarray:
        """Returns an (num_points, 3) float32 numpy array of xyz points,
        placed around self.center (the shape's *current* position)."""
        pass
