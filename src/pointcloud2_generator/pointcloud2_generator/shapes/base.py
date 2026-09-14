"""
base.py

Shared parent class for all shape generators. Handles the arguments every
shape has in common (num_points, center, seed, motion) so subclasses only
need to define their own shape-specific parameters and generate().

Motion support:
    'center' is treated as the shape's fixed base_center. On every tick,
    the node calls update_center(elapsed_seconds), which recomputes the
    shape's *current* center as base_center + motion.offset(elapsed_seconds)
    if a Motion object was provided, or leaves it at base_center otherwise.
    generate() must use self.center (not self.base_center) when placing
    the generated points.
"""

from abc import ABC, abstractmethod
import numpy as np

from pointcloud2_generator.motion import Motion


class ShapeGenerator(ABC):
    def __init__(self, num_points=1000, center=(0.0, 0.0, 0.0), seed=None, motion: Motion = None):
        self.num_points = int(num_points)
        self.base_center = np.array(center, dtype=np.float32)
        self.center = self.base_center.copy()
        self.rng = np.random.default_rng(seed)
        self.motion = motion

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