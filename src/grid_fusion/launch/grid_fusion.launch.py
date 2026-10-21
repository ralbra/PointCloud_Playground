import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('grid_fusion'), 'config', 'grid_fusion.yaml')
    return LaunchDescription([
        Node(
            package='grid_fusion',
            executable='grid_fusion_node',
            name='grid_fusion_node',
            parameters=[config],
            output='screen',
        )
    ])
