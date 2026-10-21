# playground_bringup

Launch files for the point cloud pipeline: pointcloud generators, one `pointcloud_to_grid`
instance per source, and the `grid_fusion` node. The package contains only launch files, scenes
and an RViz configuration.

```text
playground_bringup ──► pointcloud2_generator   (demo only)
                   ──► pointcloud_to_grid
                   ──► grid_fusion
```

The three packages do not depend on each other. Only this package ties them together.

## Build

```bash
cd ~/ros2_ws
colcon build --packages-select pointcloud2_generator pointcloud_to_grid grid_fusion playground_bringup
source install/setup.bash
```

## Quick start

```bash
ros2 launch playground_bringup fusion_demo.launch.py start_rviz:=true
```

This starts two generators (`front` and `rear`), two grid nodes, the fusion node and RViz. The
two scenes use different names for the same quantity (`intensity` and `reflectivity`). That
shows the per-source `value_field`.

Check it with:

```bash
ros2 topic list | grep -E 'points|fused'
ros2 topic hz /fused/intensity_grid
```

## Launch files

### `fusion_demo.launch.py`

The demo with generators.

| Argument | Default | Description |
|---|---|---|
| `generator_rate` | `10.0` | Generator publish rate in Hz. |
| `rear_enabled` | `true` | Set to `false` to start without the rear source. |
| `intensity_rule`, `height_rule` | `mean`, `max` | Fusion rules. |
| `input_timeout` | `1.0` | Seconds before a silent source is dropped. |
| `min_fresh_inputs` | `1` | Minimum live sources needed to publish. |
| `start_rviz` | `false` | Start RViz2 with the demo configuration. |
| `rviz_config` | `rviz/fusion_demo.rviz` | RViz2 configuration to load. |

### `fusion.launch.py`

For real sensors. It starts one grid node per source and the fusion node. The demo includes
this file.

| Argument | Default | Description |
|---|---|---|
| `sources` | `front:/front/points:intensity,rear:/rear/points:reflectivity` | Comma-separated `name:topic:value_field` entries. |
| `cell_size`, `length_x`, `length_y` | `0.5`, `20.0`, `30.0` | Grid geometry, shared by all sources. |
| `position_x`, `position_y` | `0.0`, `0.0` | Grid centre. |
| `intensity_factor`, `height_factor` | `100.0`, `50.0` | Value scaling, see the notes below. |
| `retention_time` | `0.0` | Cell retention of each grid node. |
| `output_prefix` | `fused` | Prefix of the fused topics. |
| `publish_rate` | `10.0` | Fusion output rate in Hz. |
| `intensity_rule`, `height_rule` | `mean`, `max` | One of `max`, `min`, `sum`, `mean`, `latest`. |
| `input_timeout` | `1.0` | Seconds before a silent source is dropped. |
| `min_fresh_inputs` | `1` | Minimum live sources needed to publish. |

Each source name must use letters, digits and underscores, and be unique. A source `front`
starts the node `grid_front` and publishes `front/intensity_grid`, `front/height_grid` and the
two GridMap topics. The fusion node reads them under the prefix `front`.

```bash
ros2 launch playground_bringup fusion.launch.py \
  sources:="lidar_a:/lidar_a/points:intensity,lidar_b:/lidar_b/points:reflectivity,lidar_c:/lidar_c/points:intensity" \
  min_fresh_inputs:=2
```

Arguments are converted to the right types in the launch file, so `input_timeout:=1` works as
well as `1.0`. An invalid source entry or a `min_fresh_inputs` outside 1 to the number of sources
stops the launch with an error.

## Output topics

`fused/intensity_grid`, `fused/height_grid` (`nav_msgs/OccupancyGrid`) and
`fused/intensity_gridmap`, `fused/height_gridmap` (`grid_map_msgs/GridMap`).

## Scenes

| File | Content |
|---|---|
| `config/scene_front.yaml` | Sphere (intensity 0.8) and cuboid (0.4). Field `intensity`. |
| `config/scene_rear.yaml` | Cuboid (0.2) overlapping the front sphere, and a cylinder (0.6). Field `reflectivity`. |

In the overlap area the fused intensity is 80 with `max` and 50 with `mean`, using the default
`intensity_factor` of 100. See the `pointcloud2_generator` README for the scene format.

## Testing the stall timeout

With the demo running, stop one generator:

```bash
pkill -f generator_rear
```

After about a second the fusion node warns that `rear` is excluded, and the cells that only the
rear source covered disappear from the fused grid. RViz keeps showing the last rear cloud
because it holds the last message. With `min_fresh_inputs:=2` the fused output stops instead.
To bring the source back:

```bash
ros2 run pointcloud2_generator generator --ros-args -r __node:=generator_rear \
  -p scene_file:=$(ros2 pkg prefix playground_bringup)/share/playground_bringup/config/scene_rear.yaml \
  -p topic_name:=rear/points
```

## Notes

- **Scaling:** grid cells are signed bytes. The defaults `intensity_factor: 100.0` and
  `height_factor: 50.0` turn 0 to 1 intensities into values the grids can hold. With a factor of
  1.0 they would truncate to 0. Keep `value * factor` within -127 to 127, and within 0 to 100 if
  you view the grids in RViz's Map display.
- **Same geometry:** all grid nodes get the same geometry arguments from `fusion.launch.py`. If
  you start grid nodes yourself, the fusion node excludes any that differ.
- **Same frame:** the clouds of all sources must be in the same frame, because no transform is
  applied anywhere in the pipeline.
- **Generators:** the demo starts the generator executables directly with explicit parameters. A
  second instance cannot use the generator's `params.yaml`, because that file is keyed to the
  node name `pointcloud_generator`.
- **Unconnected topics:** if `ros2 topic list` shows no `front/...` topics, check the node
  names. Each source should start a node called `grid_<name>`.

## License

Apache-2.0