"""
scene_loader.py

Loads an external scene description (YAML or JSON) that defines a list of
shapes to be generated as a combined PointCloud2, plus the desired
PointCloud2 field layout (point_type).

Expected scene file structure (YAML shown, JSON works the same way):

    frame_id: map
    point_type: xyzrgbi          # optional, default: 'xyz'
    intensity_field_name: reflectivity   # optional, default: 'intensity'

    shapes:
      - type: sphere
        num_points: 2000
        center: [0.0, 0.0, 0.0]
        radius: 1.0
        color: [255, 0, 0]
        intensity: 0.8
"""

import json
import os
from dataclasses import dataclass, field

import yaml

from pointcloud2_generator.pointcloud2_generator.shape_factory import ShapeFactory
from pointcloud2_generator.cloud_format import CloudFormat


@dataclass
class Scene:
    frame_id: str = "map"
    generators: list = field(default_factory=list)
    cloud_format: CloudFormat = None


class SceneLoadError(Exception):
    """Raised when a scene file cannot be loaded or parsed correctly."""
    pass


class SceneLoader:
    """Loads a scene file (YAML or JSON) and builds shape generator objects
    plus the CloudFormat describing the desired PointCloud2 field layout."""

    SUPPORTED_YAML_EXTENSIONS = (".yaml", ".yml")
    SUPPORTED_JSON_EXTENSIONS = (".json",)

    @staticmethod
    def load(path: str) -> Scene:
        if not path:
            raise SceneLoadError("No scene_file path was provided.")

        if not os.path.isfile(path):
            raise SceneLoadError(f"Scene file not found: {path}")

        raw_data = SceneLoader._read_file(path)

        if not isinstance(raw_data, dict):
            raise SceneLoadError(
                f"Scene file '{path}' must contain a mapping at the top level."
            )

        frame_id = raw_data.get("frame_id", "map")
        point_type = raw_data.get("point_type", "xyz")
        intensity_field_name = raw_data.get("intensity_field_name", "intensity")

        try:
            cloud_format = CloudFormat(
                point_type=point_type,
                intensity_field_name=intensity_field_name,
            )
        except ValueError as exc:
            raise SceneLoadError(f"Invalid point_type in '{path}': {exc}") from exc

        shape_specs = raw_data.get("shapes", [])

        if not isinstance(shape_specs, list):
            raise SceneLoadError(
                f"'shapes' in scene file '{path}' must be a list."
            )

        if len(shape_specs) == 0:
            raise SceneLoadError(
                f"Scene file '{path}' does not define any shapes."
            )

        generators = []
        for index, spec in enumerate(shape_specs):
            if not isinstance(spec, dict):
                raise SceneLoadError(
                    f"Shape entry #{index} in '{path}' must be a mapping."
                )
            try:
                generator = ShapeFactory.create(spec)
            except (KeyError, ValueError) as exc:
                raise SceneLoadError(
                    f"Invalid shape entry #{index} in '{path}': {exc}"
                ) from exc

            generators.append(generator)

        return Scene(
            frame_id=frame_id,
            generators=generators,
            cloud_format=cloud_format,
        )

    @staticmethod
    def _read_file(path: str):
        _, extension = os.path.splitext(path)
        extension = extension.lower()

        with open(path, "r") as f:
            if extension in SceneLoader.SUPPORTED_YAML_EXTENSIONS:
                return yaml.safe_load(f)
            elif extension in SceneLoader.SUPPORTED_JSON_EXTENSIONS:
                return json.load(f)
            else:
                raise SceneLoadError(
                    f"Unsupported scene file extension '{extension}'. "
                    f"Use one of: {SceneLoader.SUPPORTED_YAML_EXTENSIONS + SceneLoader.SUPPORTED_JSON_EXTENSIONS}"
                )
