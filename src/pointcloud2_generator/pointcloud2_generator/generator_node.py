import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Header
from sensor_msgs_py import point_cloud2  # helper functions

from pointcloud2_generator.shapes import create_shape

class PointCloudGenerator(Node):
    def __init__(self):
        super().__init__('pointcloud_generator')
        self.pub = self.create_publisher(PointCloud2, 'pointcloud', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Hz

        self.generator = create_shape(
            shape_name='cylinder',
            num_points=5000,
            center=(0.0, 0.0, 0.0),
            radius=1.0,
            height=3.0
        )

    def timer_callback(self):
        #cloud = self.create_example_cloud()
        #self.pub.publish(cloud)

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'map'

        points = self.generator.generate()
        msg = point_cloud2.create_cloud_xyz32(header, points.tolist())
        self.pub.publish(msg)

    def create_example_cloud(self):
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'map'
        points = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ]
        cloud = point_cloud2.create_cloud_xyz32(header, points)
        return cloud

def main(args=None):
    rclpy.init(args=args)
    node = PointCloudGenerator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()