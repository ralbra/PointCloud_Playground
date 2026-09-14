"""
shape_factory.py

Builds a single ShapeGenerator instance from a plain dict spec, as parsed
from a scene file entry. Keeping this logic separate from SceneLoader keeps
"parse the file" and "build the objects" as two distinct responsibilities.
"""

from pointcloud2_generator.shapes.sphere import SphereGenerator
from pointcloud2_generator.shapes.cuboid import CuboidGenerator
from pointcloud2_generator.shapes.cylinder import CylinderGenerator
from pointcloud2_generator.shapes.cone import ConeGenerator
from pointcloud2_generator.shapes.pyramid import PyramidGenerator


class ShapeFactory:
    """Creates a ShapeGenerator subclass instance from a shape spec dict."""

    _REGISTRY = {
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

        if shape_type not in ShapeFactory._REGISTRY:
            known = ", ".join(sorted(ShapeFactory._REGISTRY.keys()))
            raise ValueError(
                f"Unknown shape type '{shape_type}'. Known types: {known}"
            )

        common_kwargs = {
            "num_points": spec.get("num_points", 1000),
            "center": tuple(spec.get("center", (0.0, 0.0, 0.0))),
            "seed": spec.get("seed", None),
        }

        cls = ShapeFactory._REGISTRY[shape_type]
        extra_kwargs = ShapeFactory._extract_shape_kwargs(shape_type, spec)

        try:
            return cls(**common_kwargs, **extra_kwargs)
        except TypeError as exc:
            raise ValueError(
                f"Invalid or missing parameters for shape type '{shape_type}': {exc}"
            ) from exc

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
