from abc import ABC, abstractmethod
import numpy as np

class ShapeGenerator(ABC):
    def __init__(self, num_points=1000, center=(0.0, 0.0, 0.0), seed=None):
        self.num_points = int(num_points)
        self.center = np.array(center, dtype=np.float32)
        self.rng = np.random.default_rng(seed)

    @abstractmethod
    def generate(self) -> np.ndarray:
        pass