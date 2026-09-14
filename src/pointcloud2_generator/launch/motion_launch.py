"""
generator_launch.py

Launch file for the pointcloud_generator node.

- Resolves 'scene.yaml' inside this package's installed share directory,
  so you don't need to hardcode an absolute path like in params.yaml.
- Exposes launch arguments so you can override scene_file, publish_rate,
  topic_name, and frame_id from the command line without editing files.

Usage:
    ros2 launch pointcloud2_generator generator_launch.py
    ros2 launch pointcloud2_generator generator_launch.py publish_rate:=5.0
    ros2 launch pointcloud2_generator generator_launch.py scene_file:=/path/to/other_scene.yaml
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare('pointcloud2_generator')

    default_scene_file = PathJoinSubstitution([
        package_share, 'config', 'motion_scene.yaml'
    ])

    default_params_file = PathJoinSubstitution([
        package_share, 'config', 'params.yaml'
    ])

    scene_file_arg = DeclareLaunchArgument(
        'scene_file',
        default_value=default_scene_file,
        description='Path to the YAML/JSON scene file describing the shapes.'
    )

    publish_rate_arg = DeclareLaunchArgument(
        'publish_rate',
        default_value='10.0',
        description='Publish frequency in Hz.'
    )

    topic_name_arg = DeclareLaunchArgument(
        'topic_name',
        default_value='pointcloud',
        description='Output PointCloud2 topic name.'
    )

    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='',
        description="Overrides the scene file's frame_id if non-empty."
    )

    generator_node = Node(
        package='pointcloud2_generator',
        executable='generator',
        name='pointcloud_generator',
        output='screen',
        parameters=[
            default_params_file,
            {
                'scene_file': LaunchConfiguration('scene_file'),
                'publish_rate': LaunchConfiguration('publish_rate'),
                'topic_name': LaunchConfiguration('topic_name'),
                'frame_id': LaunchConfiguration('frame_id'),
            }
        ]
    )

    return LaunchDescription([
        scene_file_arg,
        publish_rate_arg,
        topic_name_arg,
        frame_id_arg,
        generator_node,
    ])