# PointCloud_Playground

A ROS 2 workspace for working with `sensor_msgs/PointCloud2` data: generate synthetic point
clouds, turn them into 2D grids and fuse several sources into one grid.

Tested with ROS 2 **Humble** only.

## Overview

```text
pointcloud2_generator ─► front/points ─► pointcloud_to_grid ─┐
                                                             ├─► grid_fusion ─► fused/*
pointcloud2_generator ─► rear/points  ─► pointcloud_to_grid ─┘
```

The generators stand in for real sensors. In a real setup, replace them with your LiDAR drivers.
Each source gets its own `pointcloud_to_grid` node, and `grid_fusion` combines the grids. The
packages do not depend on each other. `playground_bringup` is the only package that ties them
together.

## Packages

| Package | Language | Purpose |
|---|---|---|
| [`pointcloud2_generator`](src/pointcloud2_generator/README.md) | Python | Publishes configurable synthetic `PointCloud2` streams from YAML scene files: shapes, motions, colour and intensity. |
| [`pointcloud_to_grid`](src/pointcloud_to_grid/README.md) | C++ | Converts a point cloud into `OccupancyGrid` and `GridMap` messages. Any field can be the cell value, and cells can be retained over time. Derivative of [jkk-research/pointcloud_to_grid](https://github.com/jkk-research/pointcloud_to_grid). Included as a git submodule. |
| [`grid_fusion`](src/grid_fusion/README.md) | C++ | Fuses several grids with a configurable rule (`max`, `min`, `sum`, `mean`, `latest`). Sources that stop publishing are dropped after a timeout. |
| [`playground_bringup`](src/playground_bringup/README.md) | launch only | Launch files, demo scenes and an RViz configuration for the whole pipeline. |

## Getting started

### Clone

`pointcloud_to_grid` is a submodule, so clone with:

```bash
git clone --recurse-submodules [https://github.com/ralbra/PointCloud_Playground.git](https://github.com/ralbra/PointCloud_Playground.git)
```

If you already cloned without it:

```bash
git submodule update --init --recursive
```

### Dev container

The repository includes a dev container (`.devcontainer/`) for VS Code with the "Dev Containers"
extension. It supports starting RViz2 through SSH X forwarding, which needs a link to your
`.Xauthority` file in your home directory.
If you don't have this set alredy you'll need to run this script before every startup of your dev container:
```
#!/bin/bash
# wait for the session to be initialized
sleep 2

# creates a sym link to the current XAUTHORITY.
if [ -n "$XAUTHORITY" ]; then
    ln -sf "$XAUTHORITY" "$HOME/.Xauthority"
fi
```

### Build

```bash
cd ~/ros2_ws        # or the workspace root of this repository
rosdep install --from-paths src --ignore-src -y --rosdistro humble
colcon build
source install/setup.bash
```

### Run the fusion demo

```bash
ros2 launch playground_bringup fusion_demo.launch.py start_rviz:=true
```

This starts two generators, one grid node per generator, the fusion node and RViz. The fused
grids appear on `fused/intensity_grid` and `fused/height_grid`, and as `GridMap` messages on
`fused/intensity_gridmap` and `fused/height_gridmap`. Stop one generator
(`pkill -f generator_rear`) to see the timeout handling. See the
[bringup README](src/playground_bringup/README.md) for all launch arguments and for using real
sensors.

### Other launch files

| Command | What it does |
|---|---|
| `ros2 launch pointcloud2_generator generator_launch.py` | Generator only, optionally with RViz. |
| `ros2 launch pointcloud2_generator full_pipeline_launch.py` | Generator and grid conversion with a single source. |
| `ros2 launch playground_bringup fusion.launch.py sources:="..."` | Grid nodes and fusion for your own sensor topics. |

## Helper scripts

The scripts in `scripts/` also work as VS Code tasks. They source the Humble underlay and the
workspace overlay for you.

| Script | Does |
|---|---|
| `build.sh` | Deletes `build/` and `install/` and rebuilds the whole workspace with `colcon build`. |
| `launch.sh [args]` | Launches `generator_launch.py` and passes the arguments through. |
| `launch_full.sh [args]` | Launches `full_pipeline_launch.py` and passes the arguments through. |
| `run.sh` | Runs `build.sh` and then `launch.sh`. |

## Tests

```bash
colcon test
colcon test-result --all --verbose
```

`pointcloud_to_grid` and `grid_fusion` have gtest unit tests.

## Repository layout

```text
.
├── .devcontainer/           dev container (Dockerfile, devcontainer.json)
├── .vscode/                 build and launch tasks
├── scripts/                 build.sh, launch.sh, launch_full.sh, run.sh
└── src/
    ├── pointcloud2_generator/
    ├── pointcloud_to_grid/  (git submodule)
    ├── grid_fusion/
    └── playground_bringup/
```

## Credits

`pointcloud_to_grid` is derived from the original by
[JKK Research](https://github.com/jkk-research/pointcloud_to_grid). See that project for its
license.

## License

Apache-2.0.