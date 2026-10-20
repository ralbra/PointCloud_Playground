# pointcloud2_generator

A ROS 2 (Humble) Python package that publishes a universal, configurable
`sensor_msgs/PointCloud2` stream. Instead of hardcoding geometry in a node,
you describe a **scene** in an external YAML/JSON file: a list of shapes
(sphere, cuboid, cylinder, cone, pyramid), each with its own position,
random point count, optional color/intensity, optional time-based motion
(orbit, bob, linear, ellipse, square, waypoints), and a scene-wide point
field layout (`xyz`, `xyzi`, `xyzrgb`, `xyzrgbi`). A new random cloud is
generated and published on every timer tick.

---

## Features

- **5 shape generators**: sphere, cuboid, cylinder, cone, pyramid — each
  fills its volume with uniformly distributed random
  points.
- **6 motion types**: orbit, bob, ellipse, square, waypoints, linear
  (with optional bounded loop/bounce) — animate any shape's center over
  time without touching its geometry code.
- **Configurable point fields**: `xyz`, `xyzi`, `xyzrgb`, `xyzrgbi`,
  including a fully custom name for the intensity-like field (e.g.
  `reflectivity`).
- **Per-shape color and intensity**, including random per-point intensity
  within a range (`intensity_range`).
- **Multiple shapes combined into one cloud** via `numpy.concatenate`.
- **Scene-driven**: everything above is described in a YAML/JSON file, not
  Python code — swap scenes without rebuilding.
- **RViz2 integration**: the launch file starts RViz2 with a ready-made
  default view.
- **VS Code integration**: one-click build + launch via Tasks and the Run
  panel, with prompts for which scene to load.
- **Dev Container**: includes an already working Devcontainer and Dockerfile including ssh XForwarding.


---

## Package Layout

```text
pointcloud2_generator/
├── package.xml
├── setup.py
├── resource/
│   └── pointcloud2_generator
├── launch/
│   └── generator_launch.py
├── rviz/
│   └── generator.rviz
├── config/
│   ├── static_scene.yaml
│   ├── motion_scene.yaml
│   ├── colored_scene.yaml
│   └── params.yaml
└── pointcloud2_generator/
    ├── __init__.py
    ├── generator_node.py
    ├── scene_loader.py
    ├── shape_factory.py
    ├── motion_factory.py
    ├── cloud_format.py
    ├── shapes/
    │   ├── base.py
    │   ├── sphere.py
    │   ├── cuboid.py
    │   ├── cylinder.py
    │   ├── cone.py
    │   └── pyramid.py
    └── motion/
        ├── __init__.py
        ├── base.py
        ├── orbit.py
        ├── bob.py
        ├── linear.py
        ├── ellipse.py
        ├── square.py
        └── waypoints.py

# workspace root (outside this package)
├── scripts/
│   ├── build.sh
│   ├── launch.sh
│   └── run.sh
├── .devconteiner/
│   ├── devcontainer.json
│   └── Dockerfile
└── .vscode/
    ├── tasks.json
    └── launch.json
```

---

## DevContainer
This comes with an already working devcontienr you can just open with VSCode and the corresponding VSCode "Dev Containers" plugin.
Attention this needs your .Xauthority Token or a link to it in your Home directory. This needs to be set so you can start RVIZ2 from the container and pass it via ssh Xforwarding to your host Machine.
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


## Dependencies

- ROS 2 Humble
- `rclpy`, `std_msgs`, `sensor_msgs`, `sensor_msgs_py`
- `python3-yaml` (PyYAML) — for parsing scene files
- `launch`, `launch_ros` — for the launch file
- `numpy`

All of these are declared in `package.xml` as `exec_depend`s. Install
missing system dependencies with:

```bash
rosdep update
rosdep install --from-paths src --ignore-src -y --rosdistro humble
```

---

## Building

```bash
colcon build --packages-select pointcloud2_generator
source install/setup.bash
```

Or use the provided scripts (also wired into VS Code, see below):

```bash
./scripts/build.sh    # clean rebuild only
./scripts/launch.sh   # source overlay + ros2 launch (assumes already built)
./scripts/run.sh       # build.sh + launch.sh in one go
```

---

## Running

```bash
ros2 launch pointcloud2_generator generator_launch.py
```

### Launch Arguments

| Argument | Default | Description |
|---|---|---|
| `scene_file` | `config/static_scene.yaml` (installed share path) | Path to the YAML/JSON scene file. |
| `publish_rate` | `10.0` | Publish frequency in Hz. |
| `topic_name` | `pointcloud` | Output `PointCloud2` topic. |
| `frame_id` | `''` | Overrides the scene file's `frame_id` if non-empty. |
| `start_rviz` | `false` | Whether to launch RViz2 with `rviz/generator.rviz`. |
| `rviz_config` | `rviz/generator.rviz` | Path to an alternate RViz2 config. |

Example:

```bash
ros2 launch pointcloud2_generator generator_launch.py \
  scene_file:=/path/to/motion_scene.yaml \
  start_rviz:=true
```

### VS Code

- **Run and Debug panel (▶)** → pick `pointcloud2_generator: Run (choose
  scene)` from the dropdown — prompts for a scene filename (typed, under
  `config/`) and RViz2 on/off, runs the `Build` task first
  (`preLaunchTask`), then launches.

---

## Scene File Format

```yaml
frame_id: map                     # TF frame for the published cloud
point_type: xyzrgbi               # xyz | xyzi | xyzrgb | xyzrgbi
intensity_field_name: reflectivity  # optional, default: "intensity"

shapes:
  - type: sphere
    num_points: 2000
    center: [3.0, 0.0, 0.0]
    seed: 42                      # optional, for reproducible randomness
    color: [255, 0, 0]            # optional, [r, g, b] 0-255
    intensity: 0.8                # optional, fixed value for every point
    # -- OR --
    intensity_range: [0.2, 0.9]   # optional, random per-point value
    radius: 0.6
    surface_only: false           # sphere-only

    motion:                       # optional
      type: orbit
      orbit_radius: 0.6
      angular_speed: 1.0
      axis: z
```

### Scene-Level Fields

| Field | Default | Description |
|---|---|---|
| `frame_id` | `map` | TF frame written into the published `PointCloud2` header. |
| `point_type` | `xyz` | One of `xyz`, `xyzi`, `xyzrgb`, `xyzrgbi`. Determines which fields exist on every point. |
| `intensity_field_name` | `intensity` | Renames the intensity-like `PointField` (e.g. to `reflectivity`) when `point_type` includes it. |
| `shapes` | — (required) | List of shape entries, combined into one cloud. |

### Common Shape Fields (all shape types)

| Field | Default | Description |
|---|---|---|
| `type` | — (required) | `sphere`, `cuboid`, `cylinder`, `cone`, or `pyramid`. |
| `num_points` | `1000` | Number of random points generated for this shape each tick. |
| `center` | `[0, 0, 0]` | Base position. If `motion` is set, this is the anchor the motion offsets from. |
| `seed` | `None` | Seeds this shape's own RNG for reproducible point/intensity generation. |
| `color` | `None` | `[r, g, b]`, each 0-255. Used only if `point_type` includes rgb. Defaults to white if omitted but required. |
| `intensity` | `None` | Fixed value for every point. Mutually exclusive with `intensity_range`. |
| `intensity_range` | `None` | `[min, max]` — fresh random value per point, per tick. Mutually exclusive with `intensity`. |
| `motion` | `None` | Optional motion block (see below). |

### Shape-Specific Fields

| Shape | Required fields | Optional fields |
|---|---|---|
| `sphere` | `radius` | `surface_only` (bool, default `false`) |
| `cuboid` | `size_x`, `size_y`, `size_z` | — |
| `cylinder` | `radius`, `height` | — |
| `cone` | `radius`, `height` | — |
| `pyramid` | `base_size`, `height` | — |

---

## Motion Types

Add a `motion:` block to any shape to animate its center over time. All
motions return an offset added to the shape's static `center`.

| Type | Parameters | Behavior |
|---|---|---|
| `orbit` | `orbit_radius`, `angular_speed`, `axis` (`x`/`y`/`z`) | Circular path around `center`. |
| `ellipse` | `radius_a`, `radius_b`, `angular_speed`, `axis` | Elliptical path around `center`. |
| `bob` | `amplitude`, `frequency`, `axis` | Sinusoidal oscillation along one axis. |
| `square` | `side_length`, `speed`, `axis` | Constant-speed loop around a square's perimeter. |
| `waypoints` | `points` (list of `[x, y, z]`), `speed`, `loop` (bool) | Piecewise-linear path through given points, relative to `center`. |
| `linear` | `velocity` `[vx, vy, vz]`, `max_distance` (optional), `mode` (`loop` or `bounce`, default `loop`) | Straight-line drift. Unbounded if `max_distance` is omitted; otherwise resets (`loop`) or reverses (`bounce`) at that distance. |

Example — a shape bouncing back and forth along X:

```yaml
motion:
  type: linear
  velocity: [0.2, 0.0, 0.0]
  max_distance: 1.5
  mode: bounce
```

---

## Point Types (`point_type`)

| `point_type` | Fields on each point | Notes |
|---|---|---|
| `xyz` | x, y, z | Default. Ignores `color`/`intensity` even if set. |
| `xyzi` | x, y, z, i | Uses `intensity` / `intensity_range`. |
| `xyzrgb` | x, y, z, rgb | Uses `color`. RGB packed using the classic PCL/RViz float32 convention. |
| `xyzrgbi` | x, y, z, rgb, i | Uses both `color` and `intensity`/`intensity_range`. |
| `xyzi` | x, y, z, <custom> | Uses `intensity` / `intensity_range`. |

All fields are `FLOAT32`. RGB is packed as `(r << 16 | g << 8 | b)`
reinterpreted bit-for-bit as a float — this is what RViz2's default
PointCloud2 "RGB8" color transformer expects.
The xyzi point type can be given a custom name for the intensity field. This is done with the param "intensity_field_name" e.g.: 
```yaml 
point_type: xyzrgbi
intensity_field_name: reflectivity
```
---

## Included Example Scenes

| File | Demonstrates |
|---|---|
| `config/static_scene.yaml` | All 5 shapes arranged in a static ring, plain `xyz`. |
| `config/motion_scene.yaml` | All 6 motion types running simultaneously. |
| `config/colored_scene.yaml` | `xyzrgb` with a custom per-shape color. |
| `config/intensity_scene.yaml` | `xyzrgbi` with a custom `reflectivity` field and per-shape color/intensity. |
---

## Viewing in RViz2

RViz2 starts automatically (`start_rviz:=true`, the default) with
`rviz/generator.rviz`, which already has a `PointCloud2` display
subscribed to `/pointcloud` with `Fixed Frame: map`. To see color or
intensity data:

1. Select the `PointCloud2` display in the Displays panel.
2. Set **Color Transformer** to `RGB8` (for `xyzrgb*` scenes) or
   `Intensity` (for `xyzi*` scenes).
3. If using a custom intensity field name, set **Channel Name** to match
   (e.g. `reflectivity`).

---

## ROS Parameters (node-level)

| Parameter | Default | Description |
|---|---|---|
| `scene_file` | `''` (required) | Path to the scene YAML/JSON file. |
| `publish_rate` | `10.0` | Hz. |
| `topic_name` | `pointcloud` | Output topic. |
| `frame_id` | `''` | Overrides the scene file's `frame_id` if non-empty. |

---

## Troubleshooting

- **`ModuleNotFoundError ... is not a package`** — check `setup.py`'s
  `console_scripts` entry point: it must be `module:function`, not
  `module.py:function`.
- **`Cannot locate rosdep definition for [ament_python]`** — usually means
  ROS wasn't sourced before running `rosdep`, or the rosdep cache is
  stale. Run `source /opt/ros/humble/setup.bash && rosdep update` first.
- **`buildtool_depend` mismatch** — `package.xml` must declare
  `<buildtool_depend>ament_python</buildtool_depend>` (not
  `ament_cmake`) for a `setup.py`-based package, and
  `<export><build_type>ament_python</build_type></export>` must match.
- **`can't copy 'launch/...': doesn't exist or not a regular file`** —
  the file referenced in `setup.py`'s `data_files` doesn't exist at that
  exact path relative to the package root. `setup.py` in this project
  uses `glob()` so any file dropped into `launch/`, `config/`, or
  `rviz/` is picked up automatically — no manual listing needed.
- **`unexpected keyword argument 'seed'` (or similar)** — every shape
  subclass must accept `**kwargs` and call `super().__init__(**kwargs)`
  so common arguments (`num_points`, `center`, `seed`, `motion`, `color`,
  `intensity`, `intensity_range`) flow through from `ShapeGenerator`.

---

## License

Apache-2.0
