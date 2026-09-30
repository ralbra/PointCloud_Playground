"""
cloud_format.py

Defines the supported PointCloud2 field layouts ("point types") and
builds both the PointField list and the per-shape numpy point data for
a chosen layout.

Supported point_type values:
    'xyz'      -> x, y, z
    'xyzi'     -> x, y, z, <intensity_field_name>
    'xyzrgb'   -> x, y, z, rgb
    'xyzrgbi'  -> x, y, z, rgb, <intensity_field_name>

All fields are FLOAT32. RGB uses the classic PCL/RViz convention: pack
(r, g, b) each 0-255 into a single uint32 as (r << 16 | g << 8 | b), then
reinterpret those exact same bits as a float32 (NOT a numeric
conversion). This is the layout RViz2's default PointCloud2 "RGB8" color
transformer expects.
"""

import struct
import numpy as np
from sensor_msgs.msg import PointField


def pack_rgb_float(r: int, g: int, b: int) -> float:
    """Packs 0-255 r, g, b into the classic PCL/RViz float32 'rgb' encoding."""
    r = int(r) & 0xFF
    g = int(g) & 0xFF
    b = int(b) & 0xFF
    rgb_uint32 = (r << 16) | (g << 8) | b
    return struct.unpack('f', struct.pack('I', rgb_uint32))[0]


class CloudFormat:
    """Builds PointField definitions and per-shape point columns for one
    of the supported point_type layouts."""

    SUPPORTED_TYPES = ('xyz', 'xyzi', 'xyzrgb', 'xyzrgbi')

    def __init__(self, point_type: str = 'xyz', intensity_field_name: str = 'intensity'):
        point_type = point_type.lower()
        if point_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Unknown point_type '{point_type}'. "
                f"Supported: {', '.join(self.SUPPORTED_TYPES)}"
            )

        self.point_type = point_type
        self.intensity_field_name = intensity_field_name
        self.has_rgb = point_type in ('xyzrgb', 'xyzrgbi')
        self.has_intensity = point_type in ('xyzi', 'xyzrgbi')

        self.fields = self._build_fields()
        self.num_columns = len(self.fields)

    def _build_fields(self):
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        offset = 12

        if self.has_rgb:
            fields.append(PointField(
                name='rgb', offset=offset, datatype=PointField.FLOAT32, count=1
            ))
            offset += 4

        if self.has_intensity:
            fields.append(PointField(
                name=self.intensity_field_name, offset=offset,
                datatype=PointField.FLOAT32, count=1
            ))
            offset += 4

        return fields

    def build_shape_points(self, xyz: np.ndarray, color=None, intensity=None) -> np.ndarray:
        """
        xyz: (N, 3) float32 array from a ShapeGenerator.
        color: optional (r, g, b) 0-255 tuple. Ignored if this format has
               no rgb field. Defaults to white (255, 255, 255) if the
               format needs rgb but none was given.
        intensity: optional. Ignored if this format has no intensity
                   field. Accepts either:
                     - None            -> defaults to 0.0 for every point
                     - a scalar float  -> broadcast to every point
                     - an (N,) array   -> one value per point (e.g. from
                                          ShapeGenerator.get_intensity_values())

        Returns an (N, num_columns) float32 array matching self.fields order.
        """
        n = xyz.shape[0]
        columns = [xyz.astype(np.float32)]

        if self.has_rgb:
            r, g, b = color if color is not None else (255, 255, 255)
            rgb_value = pack_rgb_float(r, g, b)
            columns.append(np.full((n, 1), rgb_value, dtype=np.float32))

        if self.has_intensity:
            columns.append(self._resolve_intensity_column(intensity, n))

        return np.concatenate(columns, axis=1).astype(np.float32)

    @staticmethod
    def _resolve_intensity_column(intensity, n: int) -> np.ndarray:
        if intensity is None:
            return np.zeros((n, 1), dtype=np.float32)

        arr = np.asarray(intensity, dtype=np.float32)

        if arr.ndim == 0:
            return np.full((n, 1), float(arr), dtype=np.float32)

        if arr.shape[0] != n:
            raise ValueError(
                f"Intensity array length ({arr.shape[0]}) does not match "
                f"number of points ({n})."
            )

        return arr.reshape(n, 1)
