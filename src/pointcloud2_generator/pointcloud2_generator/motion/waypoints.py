"""
motion/waypoints.py
"""

import numpy as np
from .base import Motion


class WaypointMotion(Motion):
    """Piecewise-linear motion through a list of xyz points, at constant
    speed along the path. If 'loop' is True, the path repeats from the
    start once the end is reached; otherwise it stops at the last point."""

    def __init__(self, points, speed=1.0, loop=True):
        self.points = np.array(points, dtype=np.float32)
        self.speed = float(speed)
        self.loop = bool(loop)

        if self.points.shape[0] < 2:
            raise ValueError("WaypointMotion needs at least 2 points.")

        segment_vectors = np.diff(self.points, axis=0)
        self.segment_lengths = np.linalg.norm(segment_vectors, axis=1)
        self.total_length = float(self.segment_lengths.sum())

    def offset(self, t: float) -> np.ndarray:
        if self.total_length == 0.0:
            return self.points[0]

        dist = self.speed * t
        if self.loop:
            dist = dist % self.total_length
        else:
            dist = min(dist, self.total_length)

        cumulative = 0.0
        for i, seg_len in enumerate(self.segment_lengths):
            if dist <= cumulative + seg_len or i == len(self.segment_lengths) - 1:
                local_fraction = 0.0 if seg_len == 0.0 else (dist - cumulative) / seg_len
                return self.points[i] + (self.points[i + 1] - self.points[i]) * local_fraction
            cumulative += seg_len

        return self.points[-1]