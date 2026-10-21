# grid_fusion

A ROS 2 (Humble) node that fuses several grids into one. Inputs are the outputs of
[`pointcloud_to_grid`](../pointcloud_to_grid/README.md) nodes. The cells are combined with a
configurable rule, and sources that stop publishing are dropped after a timeout.

The package depends only on ROS message packages, not on `pointcloud_to_grid`.

```text
grid node "front" ──► front/intensity_grid, front/height_grid ─┐
                                                               ├─► grid_fusion_node ─► fused/intensity_grid, fused/height_grid
grid node "rear"  ──► rear/intensity_grid,  rear/height_grid  ─┘
```

## Features

- **Both message types:** fuses `nav_msgs/OccupancyGrid` and `grid_map_msgs/GridMap`, each as its
  own pipeline.
- **Five combine rules**, set separately for the intensity and the height grid.
- **Stall handling:** an input that has not published for `input_timeout` seconds is excluded
  until it recovers. `min_fresh_inputs` decides how many live inputs are needed to publish.
- **Safety checks:** inputs whose frame or geometry differ from the reference are excluded and
  logged.
- **Any number of sources**, configured by a list of topic prefixes.

## Build and test

```bash
cd ~/ros2_ws
colcon build --packages-select grid_fusion
colcon test --packages-select grid_fusion
colcon test-result --all --verbose
```

## Run

For a complete setup with launch files, see the `playground_bringup` package. To start the node
by hand:

```bash
ros2 run grid_fusion grid_fusion_node --ros-args \
  -p "inputs:=['front','rear']" -p intensity_rule:=mean -p height_rule:=max
```

## Topics

For every entry `<prefix>` in `inputs` the node subscribes to:

| Topic | Type |
|---|---|
| `<prefix>/intensity_grid`, `<prefix>/height_grid` | `nav_msgs/OccupancyGrid` |
| `<prefix>/intensity_gridmap`, `<prefix>/height_gridmap` | `grid_map_msgs/GridMap` |

It publishes the same four names under `output_prefix` (default `fused`). The suffixes are
parameters. Subscriptions use best-effort QoS, so they connect to both reliable and best-effort
publishers.

## Parameters

| Parameter | Default | Runtime change | Description |
|---|---|---|---|
| `inputs` | `[]` | no | Topic prefixes, one per source. At least one is required. |
| `output_prefix` | `fused` | no | Prefix of the output topics. |
| `intensity_topic`, `height_topic` | `intensity_grid`, `height_grid` | no | OccupancyGrid topic suffixes. |
| `intensity_gridmap_topic`, `height_gridmap_topic` | `intensity_gridmap`, `height_gridmap` | no | GridMap topic suffixes. |
| `fuse_occupancy_grids`, `fuse_grid_maps` | `true`, `true` | no | Which message types to fuse and publish. At least one must be true. |
| `publish_rate` | `10.0` | no | Output rate in Hz. |
| `intensity_rule`, `height_rule` | `mean`, `max` | yes | Combine rule, see below. |
| `input_timeout` | `1.0` | yes | Seconds without a new grid before an input counts as stalled. Must be `> 0`. |
| `min_fresh_inputs` | `1` | yes | Minimum number of usable inputs needed to publish. |

Invalid values stop the node at startup with a fatal message. At runtime, an invalid value is
rejected and nothing changes.

```bash
ros2 param set /grid_fusion_node intensity_rule max
ros2 param set /grid_fusion_node input_timeout 2.0
```

## Combine rules

Rules work cell by cell and ignore unknown cells (`-128`). A fused cell is unknown only if it is
unknown in every input.

| Rule | Result |
|---|---|
| `max` | Highest value. |
| `min` | Lowest value. |
| `sum` | Sum, saturated at ±127. |
| `mean` | Average of the known values, rounded to the nearest integer. |
| `latest` | Value from the most recently received input that knows the cell. Ties go to the later entry in `inputs`. |

## Stall handling

Each input's age is measured from when this node received its last grid, on the node's own
clock. Clock differences between nodes do not matter.

- **Stalled:** an input older than `input_timeout`, or stamped in the future after a clock jump,
  is excluded. The fused output continues with the remaining inputs.
- **Too few inputs:** if fewer than `min_fresh_inputs` inputs are usable, nothing is published.
  Set the value to the number of sources to stop the output as soon as one source fails.
- **Recovery:** an input that publishes again is picked up automatically.
- **Source timing:** choose `input_timeout` longer than the slowest source's publishing period.

Log messages appear only when an input changes state:

| Level | Message |
|---|---|
| WARN | `Input 'x' (...): no new grid for more than T s, excluded until it recovers` |
| WARN | `Input 'x' (...): frame or geometry differs from reference input 'y', excluded` |
| INFO | `Input 'x' (...): contributing` |
| WARN, every 5 s | `...: N of M inputs usable (need K), not publishing` |

## Requirements for the inputs

- **Same frame:** all inputs must share one `frame_id`. The node does not use TF. Put clouds into
  a common frame before the grid nodes if your sensors differ.
- **Same geometry:** resolution, size, origin and cell count must match. Give all grid nodes
  identical `cell_size`, `length_*` and `position_*`.
- **Reference input:** the first usable input in the `inputs` list defines the frame and
  geometry. Inputs that differ from it are excluded.
- **Cell convention:** int8 cells with `-128` as unknown. GridMap layers hold `cell / 127`, and
  only the first layer is used.
- **Output:** the OccupancyGrid or GridMap of the reference input is copied, so layer names and
  `info` are preserved. The stamp is the fusion node's current time.

## Code layout

| File | Content |
|---|---|
| `include/grid_fusion/fusion.hpp` | Rules, geometry check, conversions, input state, `fuseSnapshots`. Free of ROS node code, so it is unit tested directly. |
| `src/grid_fusion_node.cpp` | Parameters, subscriptions, timer, publishing and logging. |
| `test/test_fusion.cpp` | Unit tests for everything in the header. |

## Limitations

- No frame transformation (see the requirements above).
- The node itself has no automated tests, only `fusion.hpp`.
- Intensity and height are fused independently, so their inputs may come from different sources.

## License

Apache-2.0