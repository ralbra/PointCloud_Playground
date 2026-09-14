"""
motion_factory.py

Builds a single Motion instance from a plain dict spec (the 'motion' block
of a shape entry in the scene file), analogous to how ShapeFactory builds
a shape from its spec dict.
"""

from pointcloud2_generator.motion import (
    OrbitMotion,
    BobMotion,
    LinearMotion,
    EllipseMotion,
    SquareMotion,
    WaypointMotion,
)


class MotionFactory:
    """Creates a Motion subclass instance from a motion spec dict."""

    _REGISTRY = {
        "orbit": OrbitMotion,
        "bob": BobMotion,
        "linear": LinearMotion,
        "ellipse": EllipseMotion,
        "square": SquareMotion,
        "waypoints": WaypointMotion,
    }

    @staticmethod
    def create(motion_spec: dict):
        if not motion_spec:
            return None

        if "type" not in motion_spec:
            raise KeyError("Motion entry is missing required key 'type'.")

        motion_type = str(motion_spec["type"]).lower()

        if motion_type not in MotionFactory._REGISTRY:
            known = ", ".join(sorted(MotionFactory._REGISTRY.keys()))
            raise ValueError(
                f"Unknown motion type '{motion_type}'. Known types: {known}"
            )

        cls = MotionFactory._REGISTRY[motion_type]
        kwargs = {k: v for k, v in motion_spec.items() if k != "type"}

        try:
            return cls(**kwargs)
        except TypeError as exc:
            raise ValueError(
                f"Invalid or missing parameters for motion type '{motion_type}': {exc}"
            ) from exc
