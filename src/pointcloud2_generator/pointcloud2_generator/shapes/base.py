"""
base.py

Shared parent class for all shape generators. Handles the arguments every
shape has in common (num_points, center, seed) so subclasses only need to
define their own shape-specific parameters and generate().
"""

from abc import ABC, abstractmethod
import numpy as np


class ShapeGenerator(ABC):
    def __init__(self, num_points=1000, center=(0.0, 0.0, 0.0), seed=None):
        self.num_points = int(num_points)
        self.center = np.array(center, dtype=np.float32)
        self.rng = np.random.default_rng(seed)

    @abstractmethod
    def generate(self) -> np.ndarray:
        """Returns an (num_points, 3) float32 numpy array of xyz points."""
        pass