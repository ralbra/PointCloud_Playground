#!/usr/bin/env bash
#
# build.sh
#
# Build-only phase: clean + rebuild pointcloud2_generator. Meant to be
# used as a VS Code preLaunchTask, or standalone.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo ">>> Sourcing ROS 2 Humble underlay"
source /opt/ros/humble/setup.bash

echo ">>> Cleaning previous build artifacts for pointcloud2_generator"
rm -rf "${WORKSPACE_ROOT}/build/pointcloud2_generator" "${WORKSPACE_ROOT}/install/pointcloud2_generator"

echo ">>> Building pointcloud2_generator"
cd "${WORKSPACE_ROOT}"
colcon build --packages-select pointcloud2_generator
