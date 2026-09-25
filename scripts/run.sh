#!/usr/bin/env bash
#
# run.sh
#
# Convenience wrapper: build.sh followed by launch.sh, forwarding any
# arguments to launch.sh (and through to ros2 launch). Used by the
# tasks.json "Run" tasks, which prompt for scene_file/start_rviz and
# then do a full rebuild + launch in one step.
#
# Usage:
#   ./scripts/run.sh
#   ./scripts/run.sh scene_file:=/path/to/motion_scene.yaml start_rviz:=false

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/build.sh"
"${SCRIPT_DIR}/launch.sh" "$@"
