"""
generator_launch.py

Launch file for the pointcloud_generator node. Also optionally starts
RViz2 with a saved default configuration (rviz/generator.rviz) so the
PointCloud2 display is already set up on the /pointcloud topic.

Usage:
    ros2 launch pointcloud2_generator generator_launch.py
    ros2 launch pointcloud2_generator generator_launch.py publish_rate:=5.0
    ros2 launch pointcloud2_generator generator_launch.py scene_file:=/path/to/other_scene.yaml
    ros2 launch pointcloud2_generator generator_launch.py start_rviz:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare('pointcloud2_generator')

    default_scene_file = PathJoinSubstitution([
        package_share, 'config', 'scene.yaml'
    ])

    default_params_file = PathJoinSubstitution([
        package_share, 'config', 'params.yaml'
    ])

    default_rviz_config = PathJoinSubstitution([
        package_share, 'rviz', 'default.rviz'
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

    start_rviz_arg = DeclareLaunchArgument(
        'start_rviz',
        default_value='false',
        description='Whether to start RViz2 with the default config.'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config,
        description='Path to the RViz2 config file to load.'
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

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        condition=IfCondition(LaunchConfiguration('start_rviz')),
    )

    return LaunchDescription([
        scene_file_arg,
        publish_rate_arg,
        topic_name_arg,
        frame_id_arg,
        start_rviz_arg,
        rviz_config_arg,
        generator_node,
        rviz_node,
    ])
