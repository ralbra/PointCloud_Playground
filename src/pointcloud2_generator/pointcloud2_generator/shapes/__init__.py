from .sphere import SphereGenerator
from .cylinder import CylinderGenerator
from .cuboid import CuboidGenerator
from .cone import ConeGenerator
from .pyramid import PyramidGenerator

def create_shape(shape_name: str, **kwargs):
    shape_name = shape_name.lower()

    if shape_name == 'sphere':
        return SphereGenerator(**kwargs)
    if shape_name == 'cylinder':
        return CylinderGenerator(**kwargs)
    if shape_name == 'cuboid':
        return CuboidGenerator(**kwargs)
    if shape_name == 'cone':
        return ConeGenerator(**kwargs)
    if shape_name == 'pyramid':
        return PyramidGenerator(**kwargs)

    raise ValueError(f"Unknown shape: {shape_name}")