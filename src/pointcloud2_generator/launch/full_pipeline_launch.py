"""
full_pipeline_launch.py

Starts the whole chain:
    pointcloud2_generator  ->  /pointcloud  ->  pointcloud_to_grid_node  ->  grids  ->  RViz2

The generator is included from generator_launch.py (with its own RViz
disabled), so the scene_file / publish_rate / topic_name arguments behave
exactly as before.

Usage:
    ros2 launch pointcloud2_generator full_pipeline_launch.py
    ros2 launch pointcloud2_generator full_pipeline_launch.py \
        scene_file:=<path>/colored_scene.yaml value_field:=reflectivity
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    gen_share = FindPackageShare('pointcloud2_generator')

    default_scene = PathJoinSubstitution([gen_share, 'config', 'motion_scene.yaml'])
    default_rviz = PathJoinSubstitution([gen_share, 'rviz', 'pipeline.rviz'])

    args = [
        DeclareLaunchArgument('scene_file', default_value=default_scene,
                              description='Scene file for the generator.'),
        DeclareLaunchArgument('publish_rate', default_value='10.0',
                              description='Generator publish rate in Hz.'),
        DeclareLaunchArgument('topic_name', default_value='pointcloud',
                              description='PointCloud2 topic (generator output = grid input).'),
        # Grid node
        DeclareLaunchArgument('value_field', default_value='z',
                              description="Field to grid: z, intensity, reflectivity, r, g, b, ..."),
        DeclareLaunchArgument('intensity_factor', default_value='50.0',
                              description='Scale for the intensity grid (cells are int8: -128..127).'),
        DeclareLaunchArgument('height_factor', default_value='50.0',
                              description='Scale for the height grid (cells are int8: -128..127).'),
        DeclareLaunchArgument('cell_size', default_value='0.1'),
        DeclareLaunchArgument('length_x', default_value='10.0'),
        DeclareLaunchArgument('length_y', default_value='10.0'),
        DeclareLaunchArgument('retention_time', default_value='1.0',
                              description='Seconds a point keeps influencing the grid (0 = off).'),
        # RViz
        DeclareLaunchArgument('start_rviz', default_value='true'),
        DeclareLaunchArgument('rviz_config', default_value=default_rviz),
    ]

    generator = GroupAction(
        scoped=True,
        forwarding=True,   # the include can still read scene_file, publish_rate, topic_name
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([gen_share, 'launch', 'generator_launch.py'])
                ),
                launch_arguments={
                    'scene_file': LaunchConfiguration('scene_file'),
                    'publish_rate': LaunchConfiguration('publish_rate'),
                    'topic_name': LaunchConfiguration('topic_name'),
                    'start_rviz': 'false',  # now only applies inside this group
                }.items(),
            )
        ],
    )

    grid_node = Node(
        package='pointcloud_to_grid',
        executable='pointcloud_to_grid_node',
        name='pointcloud_to_grid_node',
        output='screen',
        parameters=[{
            'cloud_in_topic': ParameterValue(LaunchConfiguration('topic_name'), value_type=str),
            'value_field': ParameterValue(LaunchConfiguration('value_field'), value_type=str),
            'intensity_factor': ParameterValue(LaunchConfiguration('intensity_factor'), value_type=float),
            'height_factor': ParameterValue(LaunchConfiguration('height_factor'), value_type=float),
            'cell_size': ParameterValue(LaunchConfiguration('cell_size'), value_type=float),
            'length_x': ParameterValue(LaunchConfiguration('length_x'), value_type=float),
            'length_y': ParameterValue(LaunchConfiguration('length_y'), value_type=float),
            'position_x': 0.0,
            'position_y': 0.0,
            'verbose1': False,
            'verbose2': False,
            'mapi_topic_name': 'intensity_grid',
            'maph_topic_name': 'height_grid',
            'mapi_gridmap_topic_name': 'intensity_gridmap',
            'maph_gridmap_topic_name': 'height_gridmap',
            'retention_time': ParameterValue(LaunchConfiguration('retention_time'), value_type=float),
        }],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],  # '-d' and path must be separate items
        condition=IfCondition(LaunchConfiguration('start_rviz')),
    )

    return LaunchDescription(args + [generator, grid_node, rviz])