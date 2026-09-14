"""
motion/base.py

Shared parent class for all motion types. Mirrors shapes/base.py.
"""

from abc import ABC, abstractmethod
import numpy as np


class Motion(ABC):
    @abstractmethod
    def offset(self, t: float) -> np.ndarray:
        """Returns an xyz offset (3,) float32 array for elapsed time t (seconds)."""
        pass