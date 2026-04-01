#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import cv2
import numpy as np
import math


class ArucoDetector(Node):
    def __init__(self):
        super().__init__('aruco_detector')

        # Subscribe to camera images
        self.sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_cb,
            10
        )

        # Publish detected marker pose
        self.pub = self.create_publisher(PoseStamped, '/aruco_pose', 10)

        self.bridge = CvBridge()

        # Marker configuration
        self.marker_size = 0.046  # meters (4.6 cm)

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters_create()

        # Approximate camera intrinsics (sufficient for testing)
        self.camera_matrix = np.array([
            [528.433723449707, 0.0, 320.0],
            [0.0, 528.4337997436523, 240.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        self.dist_coeffs = np.zeros((5, 1))

        self.get_logger().info('ArUco detector started')

    def image_cb(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        corners, ids, _ = cv2.aruco.detectMarkers(
            gray,
            self.aruco_dict,
            parameters=self.aruco_params
        )

        # self.get_logger().info(f'ids detected: {ids}') 

        if ids is None:
            return

        # Estimate pose of the first detected marker
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            corners,
            self.marker_size,
            self.camera_matrix,
            self.dist_coeffs
        )

        tvec = tvecs[0][0]

        # Distance straight ahead (meters)
        distance = float(tvec[2])

        # Yaw error (left/right offset)
        yaw = math.atan2(tvec[0], tvec[2])

        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = 'camera_link'

        pose.pose.position.z = distance
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.pub.publish(pose)


def main():
    rclpy.init()
    node = ArucoDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

