"""
motion/linear.py
"""

import numpy as np
from .base import Motion


class LinearMotion(Motion):
    """Motion along a fixed direction vector at constant speed.

    By default (max_distance=None), the object drifts indefinitely in a
    straight line.

    If max_distance is set, the traveled distance is capped/wrapped
    according to 'mode':
        - 'loop':   travels straight out to max_distance, then jumps back
                    to the starting point and repeats (teleport reset).
        - 'bounce': travels straight out to max_distance, then reverses
                    direction and travels back to the start, repeating
                    back and forth indefinitely (no teleporting).
    """

    def __init__(self, velocity=(0.0, 0.0, 0.0), max_distance=None, mode='loop'):
        self.velocity = np.array(velocity, dtype=np.float32)
        self.speed = float(np.linalg.norm(self.velocity))
        self.direction = (
            self.velocity / self.speed if self.speed > 0.0
            else np.zeros(3, dtype=np.float32)
        )

        self.max_distance = float(max_distance) if max_distance is not None else None
        self.mode = mode.lower()

        if self.mode not in ('loop', 'bounce'):
            raise ValueError(f"Invalid linear motion mode '{mode}'. Use 'loop' or 'bounce'.")

        if self.max_distance is not None and self.max_distance <= 0.0:
            raise ValueError("max_distance must be a positive number if set.")

    def offset(self, t: float) -> np.ndarray:
        if self.speed == 0.0:
            return np.zeros(3, dtype=np.float32)

        distance = self.speed * t

        if self.max_distance is None:
            return self.direction * distance

        if self.mode == 'loop':
            distance = distance % self.max_distance
        else:  # 'bounce'
            cycle = 2.0 * self.max_distance
            distance = distance % cycle
            if distance > self.max_distance:
                distance = cycle - distance

        return self.direction * distance