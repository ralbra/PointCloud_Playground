"""
shape_factory.py

Builds a single ShapeGenerator instance (optionally with a Motion object,
built via MotionFactory, and optional color/intensity) from a plain dict
spec, as parsed from a scene file entry.
"""

from pointcloud2_generator.shapes.sphere import SphereGenerator
from pointcloud2_generator.shapes.cuboid import CuboidGenerator
from pointcloud2_generator.shapes.cylinder import CylinderGenerator
from pointcloud2_generator.shapes.cone import ConeGenerator
from pointcloud2_generator.shapes.pyramid import PyramidGenerator

from pointcloud2_generator.motion.motion_factory import MotionFactory


class ShapeFactory:
    """Creates a ShapeGenerator subclass instance from a shape spec dict."""

    _SHAPE_REGISTRY = {
        "sphere": SphereGenerator,
        "cuboid": CuboidGenerator,
        "cylinder": CylinderGenerator,
        "cone": ConeGenerator,
        "pyramid": PyramidGenerator,
    }

    @staticmethod
    def create(spec: dict):
        if "type" not in spec:
            raise KeyError("Shape entry is missing required key 'type'.")

        shape_type = str(spec["type"]).lower()

        if shape_type not in ShapeFactory._SHAPE_REGISTRY:
            known = ", ".join(sorted(ShapeFactory._SHAPE_REGISTRY.keys()))
            raise ValueError(
                f"Unknown shape type '{shape_type}'. Known types: {known}"
            )

        common_kwargs = {
            "num_points": spec.get("num_points", 1000),
            "center": tuple(spec.get("center", (0.0, 0.0, 0.0))),
            "seed": spec.get("seed", None),
            "motion": MotionFactory.create(spec.get("motion")),
            "color": ShapeFactory._parse_color(spec.get("color")),
            "intensity": spec.get("intensity", None),
        }

        cls = ShapeFactory._SHAPE_REGISTRY[shape_type]
        extra_kwargs = ShapeFactory._extract_shape_kwargs(shape_type, spec)

        try:
            return cls(**common_kwargs, **extra_kwargs)
        except TypeError as exc:
            raise ValueError(
                f"Invalid or missing parameters for shape type '{shape_type}': {exc}"
            ) from exc

    @staticmethod
    def _parse_color(color_spec):
        if color_spec is None:
            return None
        if len(color_spec) != 3:
            raise ValueError(
                f"'color' must have exactly 3 values [r, g, b], got: {color_spec}"
            )
        for channel in color_spec:
            if not (0 <= channel <= 255):
                raise ValueError(
                    f"'color' channel values must be in range 0-255, got: {color_spec}"
                )
        return tuple(int(c) for c in color_spec)

    @staticmethod
    def _extract_shape_kwargs(shape_type: str, spec: dict) -> dict:
        """Pulls the shape-specific required/optional fields out of spec."""

        if shape_type == "sphere":
            return {
                "radius": ShapeFactory._require(spec, "radius"),
                "surface_only": spec.get("surface_only", False),
            }

        if shape_type == "cuboid":
            return {
                "size_x": ShapeFactory._require(spec, "size_x"),
                "size_y": ShapeFactory._require(spec, "size_y"),
                "size_z": ShapeFactory._require(spec, "size_z"),
            }

        if shape_type == "cylinder":
            return {
                "radius": ShapeFactory._require(spec, "radius"),
                "height": ShapeFactory._require(spec, "height"),
            }

        if shape_type == "cone":
            return {
                "radius": ShapeFactory._require(spec, "radius"),
                "height": ShapeFactory._require(spec, "height"),
            }

        if shape_type == "pyramid":
            return {
                "base_size": ShapeFactory._require(spec, "base_size"),
                "height": ShapeFactory._require(spec, "height"),
            }

        return {}

    @staticmethod
    def _require(spec: dict, key: str):
        if key not in spec:
            raise KeyError(f"Missing required field '{key}' for this shape type.")
        return spec[key]
