#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseStamped
import math
import time


class DockPIDController(Node):
    def __init__(self):
        super().__init__('dock_pid_controller')

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(
            PoseStamped,
            '/aruco_pose',
            self.aruco_cb,
            10
        )

        # PID gains (to be tuned on real robot)
        self.kp_yaw = 2.0
        self.kd_yaw = 0.2

        self.max_angular_speed = 0.3  # rad/s
        self.yaw_tolerance = math.radians(2.0)

        self.prev_yaw_error = 0.0
        self.prev_time = time.time()

        self.marker_visible = False
        self.yaw_error = 0.0

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info('Docking PID Controller started')

    def aruco_cb(self, msg):
        # Extract yaw from quaternion (z, w only)
        z = msg.pose.orientation.z
        w = msg.pose.orientation.w
        self.yaw_error = 2.0 * math.atan2(z, w)
        self.marker_visible = True

    def control_loop(self):
        cmd = Twist()

        if not self.marker_visible:
            self.get_logger().info('Idle (waiting for marker)')
            self.cmd_pub.publish(cmd)
            return

        now = time.time()
        dt = now - self.prev_time
        self.prev_time = now

        # PID for yaw
        yaw_derivative = (self.yaw_error - self.prev_yaw_error) / dt
        angular_cmd = (
            self.kp_yaw * self.yaw_error +
            self.kd_yaw * yaw_derivative
        )

        self.prev_yaw_error = self.yaw_error

        # Clamp angular velocity
        angular_cmd = max(
            min(angular_cmd, self.max_angular_speed),
            -self.max_angular_speed
        )

        if abs(self.yaw_error) > self.yaw_tolerance:
            cmd.angular.z = angular_cmd
            self.get_logger().info(
                f'Aligning | Yaw error: {math.degrees(self.yaw_error):.2f} deg'
            )
        else:
            cmd.angular.z = 0.0
            self.get_logger().info('Yaw aligned')

        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = DockPIDController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

