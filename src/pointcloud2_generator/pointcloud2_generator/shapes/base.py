"""
shapes/base.py

Shared parent class for all shape generators. Handles the arguments every
shape has in common: num_points, center, seed, motion, and the optional
per-shape color/intensity used when the scene's point_type includes an
rgb and/or intensity field (see cloud_format.py).

Intensity can be either:
    - a fixed scalar ('intensity': 0.8) -- same value for every point, or
    - a random range ('intensity_range': [0.2, 0.9]) -- a fresh random
      value per point, drawn each tick from the shape's own seeded RNG.
Only one of the two may be set at a time.
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
        intensity_range=None,
    ):
        self.num_points = int(num_points)
        self.base_center = np.array(center, dtype=np.float32)
        self.center = self.base_center.copy()
        self.rng = np.random.default_rng(seed)
        self.motion = motion

        # color: optional (r, g, b) tuple, 0-255 each. Only used if the
        # scene's point_type includes an rgb field.
        self.color = tuple(color) if color is not None else None

        if intensity is not None and intensity_range is not None:
            raise ValueError(
                "Specify either 'intensity' or 'intensity_range', not both."
            )

        self.intensity = float(intensity) if intensity is not None else None

        if intensity_range is not None:
            if len(intensity_range) != 2:
                raise ValueError(
                    f"'intensity_range' must be [min, max], got: {intensity_range}"
                )
            low, high = float(intensity_range[0]), float(intensity_range[1])
            if low > high:
                raise ValueError(
                    f"'intensity_range' min must be <= max, got: {intensity_range}"
                )
            self.intensity_range = (low, high)
        else:
            self.intensity_range = None

    def update_center(self, elapsed_seconds: float):
        """Recomputes self.center for the given elapsed time. Call this
        once per publish tick, before generate()."""
        if self.motion is not None:
            self.center = self.base_center + self.motion.offset(elapsed_seconds)
        else:
            self.center = self.base_center

    def get_intensity_values(self):
        """Returns an (num_points,) float32 array of intensity values for
        the current tick, or None if this shape has no intensity/
        intensity_range configured.

        If intensity_range is set, draws a fresh uniform random value per
        point on every call (so it varies each publish tick, same as the
        geometry itself). If a fixed intensity is set, returns that value
        broadcast to every point."""
        if self.intensity_range is not None:
            low, high = self.intensity_range
            return self.rng.uniform(low, high, size=self.num_points).astype(np.float32)

        if self.intensity is not None:
            return np.full(self.num_points, self.intensity, dtype=np.float32)

        return None

    @abstractmethod
    def generate(self) -> np.ndarray:
        """Returns an (num_points, 3) float32 numpy array of xyz points,
        placed around self.center (the shape's *current* position)."""
        pass
