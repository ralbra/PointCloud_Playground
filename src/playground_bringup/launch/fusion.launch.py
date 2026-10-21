import re

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

NAME_PATTERN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')

# (name, default, description)
ARGUMENTS = [
    ('sources', 'front:/front/points:intensity,rear:/rear/points:reflectivity',
     'Comma separated name:topic:value_field entries, one per pointcloud source'),
    ('cell_size', '0.5', 'Grid cell size [m], identical for all sources'),
    ('length_x', '20.0', 'Grid length in x [m]'),
    ('length_y', '30.0', 'Grid length in y [m]'),
    ('position_x', '0.0', 'Grid centre x [m]'),
    ('position_y', '0.0', 'Grid centre y [m]'),
    ('intensity_factor', '100.0', 'Scale applied to the value before it becomes an int8 cell'),
    ('height_factor', '50.0', 'Scale for the height grid'),
    ('retention_time', '0.0', 'Seconds a cell is kept by each grid node (0 = no retention)'),
    ('output_prefix', 'fused', 'Prefix of the fused output topics'),
    ('publish_rate', '10.0', 'Fusion output rate [Hz]'),
    ('intensity_rule', 'mean', 'max | min | sum | mean | latest'),
    ('height_rule', 'max', 'max | min | sum | mean | latest'),
    ('input_timeout', '1.0', 'Seconds without a new grid before a source is dropped'),
    ('min_fresh_inputs', '1', 'Minimum number of live sources needed to publish'),
]


def parse_sources(text):
    sources = []
    for item in text.split(','):
        item = item.strip()
        if not item:
            continue
        parts = item.split(':')
        if len(parts) != 3 or not all(parts):
            raise RuntimeError(
                'Invalid source {!r}: expected name:topic:value_field'.format(item))
        name, topic, field = parts
        if not NAME_PATTERN.fullmatch(name):
            raise RuntimeError(
                'Invalid source name {!r}: use letters, digits and underscores'.format(name))
        sources.append((name, topic, field))
    if not sources:
        raise RuntimeError('No sources given')
    names = [name for name, _, _ in sources]
    if len(set(names)) != len(names):
        raise RuntimeError('Source names must be unique')
    return sources


def launch_setup(context):
    def arg(name):
        return LaunchConfiguration(name).perform(context)

    sources = parse_sources(arg('sources'))
    min_fresh_inputs = int(arg('min_fresh_inputs'))
    if not 1 <= min_fresh_inputs <= len(sources):
        raise RuntimeError('min_fresh_inputs must be between 1 and the number of sources')

    # every grid node must use identical geometry, or the fusion node rejects it
    grid_params = {
        'cell_size': float(arg('cell_size')),
        'length_x': float(arg('length_x')),
        'length_y': float(arg('length_y')),
        'position_x': float(arg('position_x')),
        'position_y': float(arg('position_y')),
        'intensity_factor': float(arg('intensity_factor')),
        'height_factor': float(arg('height_factor')),
        'retention_time': float(arg('retention_time')),
        'verbose1': False,
        'verbose2': False,
    }

    actions = []
    for name, topic, field in sources:
        params = dict(
            grid_params,
            cloud_in_topic=topic,
            value_field=field,
            mapi_topic_name=name + '/intensity_grid',
            maph_topic_name=name + '/height_grid',
            mapi_gridmap_topic_name=name + '/intensity_gridmap',
            maph_gridmap_topic_name=name + '/height_gridmap',
        )
        actions.append(Node(
            package='pointcloud_to_grid',
            executable='pointcloud_to_grid_node',
            name='grid_' + name,
            output='screen',
            parameters=[params],
        ))

    actions.append(Node(
        package='grid_fusion',
        executable='grid_fusion_node',
        name='grid_fusion_node',
        output='screen',
        parameters=[{
            'inputs': [name for name, _, _ in sources],
            'output_prefix': arg('output_prefix'),
            'publish_rate': float(arg('publish_rate')),
            'intensity_rule': arg('intensity_rule'),
            'height_rule': arg('height_rule'),
            'input_timeout': float(arg('input_timeout')),
            'min_fresh_inputs': min_fresh_inputs,
        }],
    ))
    return actions


def generate_launch_description():
    declarations = [
        DeclareLaunchArgument(name, default_value=default, description=description)
        for name, default, description in ARGUMENTS
    ]
    return LaunchDescription(declarations + [OpaqueFunction(function=launch_setup)])