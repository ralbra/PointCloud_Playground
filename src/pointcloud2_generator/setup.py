import os
from glob import glob

from setuptools import setup, find_packages

package_name = 'pointcloud2_generator'


def all_files(directory, patterns):
    """Collects every file under `directory` matching any of `patterns`
    (non-recursive). Returns [] if the directory doesn't exist or is empty,
    so a missing/renamed file never breaks the build -- it's just not
    installed."""
    matches = []
    for pattern in patterns:
        matches.extend(glob(os.path.join(directory, pattern)))
    return matches


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test', 'test.*']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # All launch files (*.py) under launch/, installed flat into
        # share/<package_name>/launch/
        (os.path.join('share', package_name, 'launch'),
            all_files('launch', ['*.py'])),

        # All scene/config files (YAML + JSON) under config/, installed
        # flat into share/<package_name>/config/
        (os.path.join('share', package_name, 'config'),
            all_files('config', ['*.yaml', '*.yml', '*.json'])),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='you@example.com',
    description='Universal PointCloud2 generator for ROS 2, builds combined '
                 'point clouds from a scene file describing multiple shapes '
                 '(sphere, cuboid, cylinder, cone, pyramid) with optional '
                 'time-based motion.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'generator = pointcloud2_generator.generator_node:main',
        ],
    },
)