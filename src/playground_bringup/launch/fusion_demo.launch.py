import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

DEMO_SOURCES = 'front:front/points:intensity,rear:rear/points:reflectivity'


def generate_launch_description():
    share = get_package_share_directory('playground_bringup')
    scenes = os.path.join(share, 'config')
    rate = ParameterValue(LaunchConfiguration('generator_rate'), value_type=float)

    def generator(name, scene, condition=None):
        # explicit parameters: the generator's params.yaml is keyed to its default node name
        return Node(
            package='pointcloud2_generator',
            executable='generator',
            name='generator_' + name,
            output='screen',
            condition=condition,
            parameters=[{
                'scene_file': os.path.join(scenes, scene),
                'publish_rate': rate,
                'topic_name': name + '/points',
            }],
        )

    fusion = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(share, 'launch', 'fusion.launch.py')),
        launch_arguments={
            'sources': DEMO_SOURCES,
            'intensity_rule': LaunchConfiguration('intensity_rule'),
            'height_rule': LaunchConfiguration('height_rule'),
            'input_timeout': LaunchConfiguration('input_timeout'),
            'min_fresh_inputs': LaunchConfiguration('min_fresh_inputs'),
        }.items(),
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        condition=IfCondition(LaunchConfiguration('start_rviz')),
    )

    return LaunchDescription([
        DeclareLaunchArgument('generator_rate', default_value='10.0'),
        DeclareLaunchArgument('rear_enabled', default_value='true',
                              description='Set to false to start without the rear source'),
        DeclareLaunchArgument('intensity_rule', default_value='mean'),
        DeclareLaunchArgument('height_rule', default_value='max'),
        DeclareLaunchArgument('input_timeout', default_value='1.0'),
        DeclareLaunchArgument('min_fresh_inputs', default_value='1'),
        DeclareLaunchArgument('start_rviz', default_value='false',
                              description='Whether to start RViz2 with the demo config'),
        DeclareLaunchArgument('rviz_config',
                              default_value=os.path.join(share, 'rviz', 'fusion_demo.rviz'),
                              description='Path to the RViz2 config file to load'),
        generator('front', 'scene_front.yaml'),
        generator('rear', 'scene_rear.yaml',
                  condition=IfCondition(LaunchConfiguration('rear_enabled'))),
        fusion,
        rviz,
    ])