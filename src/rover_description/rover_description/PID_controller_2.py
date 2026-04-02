#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseStamped
import math
import time

class DockPIDController(Node):
    def __init__(self):
        super().__init__('dock_pid_controller_2')


        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(
            PoseStamped,
            '/aruco_pose',
            self.aruco_cb,
            10
        )

        # --- PID GAINS ---
        self.kp_yaw = 1.2
        self.kd_yaw = 0.15

        self.max_angular_speed = 0.4
        self.yaw_tolerance = math.radians(3.0)

        # --- DISTANCE CONTROL ---
        self.kp_dist = 0.5   # NEW
        self.max_linear_speed = 0.2
        self.stop_distance = 0.10  # 10 cm

        # --- STATE ---
        self.prev_yaw_error = 0.0
        self.prev_time = time.time()

        self.marker_visible = False
        self.yaw_error = 0.0
        self.distance = 999.0
        self.last_seen_time = time.time()

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info('Docking PID Controller started')

    def aruco_cb(self, msg):
        x = msg.pose.position.x
        z = msg.pose.position.z

        self.yaw_error = math.atan2(x, z)
        self.distance = z

        self.marker_visible = True
        self.last_seen_time = time.time()

    def control_loop(self):
        cmd = Twist()

        # --- Marker timeout ---
        if time.time() - self.last_seen_time > 1.0:
            self.marker_visible = False

        if not self.marker_visible:
            self.get_logger().info('Searching...', throttle_duration_sec=1.0)
            self.cmd_pub.publish(cmd)
            return

        now = time.time()
        dt = now - self.prev_time
        self.prev_time = now

        if dt == 0:
            return

        # --- YAW PID ---
        yaw_derivative = (self.yaw_error - self.prev_yaw_error) / dt
        angular_cmd = (
            self.kp_yaw * self.yaw_error +
            self.kd_yaw * yaw_derivative
        )

        self.prev_yaw_error = self.yaw_error

        angular_cmd = max(
            min(angular_cmd, self.max_angular_speed),
            -self.max_angular_speed
        )

        # --- CONTROL LOGIC ---
        if abs(self.yaw_error) > self.yaw_tolerance:
            # Rotate only
            cmd.angular.z = angular_cmd
            cmd.linear.x = 0.0

        else:
            # --- DISTANCE CONTROL ---
            distance_error = self.distance - self.stop_distance

            if distance_error > 0:
                # Proportional speed (slows near target)
                linear_cmd = self.kp_dist * distance_error

                linear_cmd = max(
                    min(linear_cmd, self.max_linear_speed),
                    0.05  # minimum speed to avoid stalling
                )

                cmd.linear.x = linear_cmd
                cmd.angular.z = 0.0

                self.get_logger().info(
                    f'Approaching | Dist: {self.distance:.2f} m',
                    throttle_duration_sec=0.5
                )

            else:
                # STOP
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0

                self.get_logger().info(
                    'Docked at 10 cm ✅',
                    throttle_duration_sec=1.0
                )

        self.cmd_pub.publish(cmd)

def main():
    rclpy.init()
    node = DockPIDController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

