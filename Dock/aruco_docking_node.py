import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2
import cv2.aruco as aruco
import numpy as np
import math

class ArucoDocking(Node):

    def __init__(self):
        super().__init__('aruco_docking_node')

        # -------------------------
        # 1. PARAMETERS (Load from YAML or Default)
        # -------------------------
        self.declare_parameter('marker_id', 10)
        self.declare_parameter('marker_size', 0.15)
        self.declare_parameter('desired_distance', 0.5)
        self.declare_parameter('camera_topic', '/camera/image_raw')

        self.marker_id = self.get_parameter('marker_id').value
        self.marker_size = self.get_parameter('marker_size').value
        self.desired_distance = self.get_parameter('desired_distance').value
        self.camera_topic = self.get_parameter('camera_topic').value

        # Control PID / Thresholds
        self.linear_speed = 0.15      # Slower for safety
        self.angular_speed = 0.4
        self.search_angular_speed = 0.2
        
        self.angle_tol = 0.05         # ~3 degrees tolerance
        self.dist_tol = 0.02          # 2 cm tolerance

        # -------------------------
        # 2. CAMERA CALIBRATION (OBSBOT MEET SE - 1080p)
        # -------------------------
        # Transferred from your standalone script
        self.camera_matrix = np.array([
            [1320.0,    0.0, 960.0],
            [   0.0, 1320.0, 540.0],
            [   0.0,    0.0,   1.0]
        ], dtype=np.float32)

        self.dist_coeffs = np.zeros((5, 1))

        # -------------------------
        # 3. SETUP
        # -------------------------
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        self.aruco_params = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        self.bridge = CvBridge()
        
        # Publishers & Subscribers
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.image_sub = self.create_subscription(
            Image, 
            self.camera_topic, 
            self.image_callback, 
            10
        )
        
        self.get_logger().info(f"Docking Node Started. ID: {self.marker_id} | Dist: {self.desired_distance}m")

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"CV Bridge Error: {e}")
            return

        # SAFETY CHECK: Ensure resolution matches calibration
        h, w = frame.shape[:2]
        if w != 1920:
            self.get_logger().warn(f"Camera is {w}x{h}. Calibration expects 1920x1080! Distances will be wrong.")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)
        
        cmd = Twist()

        if ids is not None and self.marker_id in ids:
            # Get specific marker index
            idx = np.where(ids == self.marker_id)[0][0]
            marker_corners = corners[idx]

            # Estimate Pose
            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                marker_corners, 
                self.marker_size, 
                self.camera_matrix, 
                self.dist_coeffs
            )

            # Extract Z (Distance) and X (Lateral offset)
            # tvec format is [[x, y, z]]
            x = tvecs[0][0][0]
            z = tvecs[0][0][2]

            distance = z
            angle = math.atan2(x, z) # radians

            self.get_logger().info(f"Target Found -> Dist: {distance:.2f}m | Angle: {math.degrees(angle):.1f} deg")

            # --- CONTROL STATE MACHINE ---

            # 1. ALIGN (Rotate in place if angle is too large)
            if abs(angle) > self.angle_tol:
                cmd.linear.x = 0.0
                # In standard camera frames: +Angle means marker is to the RIGHT.
                # To face right, robot turns LEFT (+Angular Z).
                # Check your robot's rotation direction; you might need to flip the sign below.
                cmd.angular.z = -self.angular_speed if angle > 0 else self.angular_speed
            
            # 2. APPROACH (Drive forward if not at desired distance)
            elif abs(distance - self.desired_distance) > self.dist_tol:
                # Simple P-Controller for smooth approach
                cmd.linear.x = self.linear_speed if distance > self.desired_distance else -self.linear_speed
                # Keep correcting angle while driving
                cmd.angular.z = -2.0 * angle 
            
            # 3. STOP (Docked)
            else:
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
                self.get_logger().info("✅ DOCKED SUCCESSFULLY")

        else:
            # 4. SEARCH (Rotate slowly to find marker)
            cmd.linear.x = 0.0
            cmd.angular.z = self.search_angular_speed
            self.get_logger().info("Searching for marker...")

        self.cmd_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = ArucoDocking()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()