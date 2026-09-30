"""
generator_node.py

ROS 2 (Humble) node that publishes a combined PointCloud2 built from a
list of shapes defined in an external YAML or JSON scene file. Shapes may
optionally define a 'motion' block (animates center over time) and/or
'color' / 'intensity' / 'intensity_range' values, used according to the
scene's 'point_type' (xyz, xyzi, xyzrgb, or xyzrgbi -- see cloud_format.py).

ROS parameters:
    scene_file    (string)  Path to the YAML/JSON scene file. Required.
    publish_rate  (double)  Publish frequency in Hz. Default: 10.0
    topic_name    (string)  Output topic name. Default: 'pointcloud'
    frame_id      (string)  Overrides the frame_id from the scene file
                             if set to a non-empty string. Default: ''

On every timer tick:
    1. Elapsed time since node start is computed via the node's own clock.
    2. Each shape's update_center(elapsed_seconds) is called, applying its
       motion (if any).
    3. Each shape's generate() produces fresh (N, 3) xyz points around its
       current center.
    4. Each shape's get_intensity_values() produces either a fixed value,
       a fresh random value per point (if intensity_range is set), or None.
    5. cloud_format.build_shape_points() expands xyz + color + intensity
       into the full per-point column layout.
    6. All shapes' point arrays are concatenated and published as one
       PointCloud2, using the scene's PointField layout.
"""

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2

from pointcloud2_generator.scene_loader import SceneLoader, SceneLoadError


class PointCloudGeneratorNode(Node):
    def __init__(self):
        super().__init__('pointcloud_generator')

        self.declare_parameter('scene_file', '')
        self.declare_parameter('publish_rate', 10.0)
        self.declare_parameter('topic_name', 'pointcloud')
        self.declare_parameter('frame_id', '')

        scene_file = self.get_parameter('scene_file').get_parameter_value().string_value
        publish_rate = self.get_parameter('publish_rate').get_parameter_value().double_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        frame_id_override = self.get_parameter('frame_id').get_parameter_value().string_value

        if not scene_file:
            self.get_logger().fatal(
                "Parameter 'scene_file' is empty. Provide a path to a YAML/JSON scene file."
            )
            raise SystemExit(1)

        try:
            self.scene = SceneLoader.load(scene_file)
        except SceneLoadError as exc:
            self.get_logger().fatal(f"Failed to load scene file: {exc}")
            raise SystemExit(1)

        self.frame_id = frame_id_override if frame_id_override else self.scene.frame_id

        self.get_logger().info(
            f"Loaded {len(self.scene.generators)} shape(s) from '{scene_file}' "
            f"(frame_id='{self.frame_id}', point_type='{self.scene.cloud_format.point_type}', "
            f"rate={publish_rate} Hz)."
        )

        self.publisher_ = self.create_publisher(PointCloud2, topic_name, 10)

        self._start_time = self.get_clock().now()

        timer_period = 1.0 / publish_rate if publish_rate > 0.0 else 0.1
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        elapsed_seconds = self._get_elapsed_seconds()

        for generator in self.scene.generators:
            generator.update_center(elapsed_seconds)

        combined_points = self.generate_combined_cloud()

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = self.frame_id

        msg = point_cloud2.create_cloud(
            header, self.scene.cloud_format.fields, combined_points
        )
        self.publisher_.publish(msg)

    def _get_elapsed_seconds(self) -> float:
        now = self.get_clock().now()
        return (now - self._start_time).nanoseconds / 1e9

    def generate_combined_cloud(self) -> np.ndarray:
        cloud_format = self.scene.cloud_format
        num_columns = cloud_format.num_columns

        if not self.scene.generators:
            return np.empty((0, num_columns), dtype=np.float32)

        shape_arrays = [
            cloud_format.build_shape_points(
                generator.generate(),
                color=generator.color,
                intensity=generator.get_intensity_values(),
            )
            for generator in self.scene.generators
        ]
        return np.concatenate(shape_arrays, axis=0).astype(np.float32)


def main(args=None):
    rclpy.init(args=args)
    try:
        node = PointCloudGeneratorNode()
    except SystemExit:
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
