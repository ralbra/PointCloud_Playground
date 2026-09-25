#!/usr/bin/env bash
#
# launch.sh
#
# Launch-only phase: source overlay + ros2 launch. Assumes the package
# has already been built (e.g. by build.sh, run as a preLaunchTask).
#
# Usage:
#   ./scripts/launch.sh
#   ./scripts/launch.sh scene_file:=/path/to/motion_scene.yaml
#   ./scripts/launch.sh start_rviz:=false

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo ">>> Sourcing ROS 2 Humble underlay"
source /opt/ros/humble/setup.bash

echo ">>> Sourcing workspace overlay"
source "${WORKSPACE_ROOT}/install/setup.bash"

echo ">>> Launching pointcloud2_generator"
ros2 launch pointcloud2_generator generator_launch.py "$@"
