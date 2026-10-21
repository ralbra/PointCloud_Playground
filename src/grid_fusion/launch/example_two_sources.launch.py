from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def grid_node(name, topic_arg, field_arg, common):
    return Node(
        package='pointcloud_to_grid',
        executable='pointcloud_to_grid_node',
        name=f'grid_{name}',
        parameters=[{
            **common,
            'cloud_in_topic': LaunchConfiguration(topic_arg),
            'value_field': LaunchConfiguration(field_arg),
            'mapi_topic_name': f'{name}/intensity_grid',
            'maph_topic_name': f'{name}/height_grid',
            'mapi_gridmap_topic_name': f'{name}/intensity_gridmap',
            'maph_gridmap_topic_name': f'{name}/height_gridmap',
        }],
        output='screen',
    )


def generate_launch_description():
    common = {
        'cell_size': LaunchConfiguration('cell_size'),
        'length_x': LaunchConfiguration('length_x'),
        'length_y': LaunchConfiguration('length_y'),
    }
    args = [
        DeclareLaunchArgument('front_topic', default_value='/front/points'),
        DeclareLaunchArgument('front_field', default_value='intensity'),
        DeclareLaunchArgument('rear_topic', default_value='/rear/points'),
        DeclareLaunchArgument('rear_field', default_value='reflectivity'),
        DeclareLaunchArgument('cell_size', default_value='0.5'),
        DeclareLaunchArgument('length_x', default_value='20.0'),
        DeclareLaunchArgument('length_y', default_value='30.0'),
        DeclareLaunchArgument('intensity_rule', default_value='mean'),
        DeclareLaunchArgument('height_rule', default_value='max'),
        DeclareLaunchArgument('input_timeout', default_value='1.0'),
        DeclareLaunchArgument('min_fresh_inputs', default_value='1'),
    ]
    fusion = Node(
        package='grid_fusion',
        executable='grid_fusion_node',
        name='grid_fusion_node',
        parameters=[{
            'inputs': ['front', 'rear'],
            'intensity_rule': LaunchConfiguration('intensity_rule'),
            'height_rule': LaunchConfiguration('height_rule'),
            'input_timeout': LaunchConfiguration('input_timeout'),
            'min_fresh_inputs': LaunchConfiguration('min_fresh_inputs'),
        }],
        output='screen',
    )
    return LaunchDescription(args + [
        grid_node('front', 'front_topic', 'front_field', common),
        grid_node('rear', 'rear_topic', 'rear_field', common),
        fusion,
    ])
