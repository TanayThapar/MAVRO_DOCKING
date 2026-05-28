import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class RoverCameraNode(Node):
    def __init__(self):
        super().__init__('rover1_camera_node')

        # Publisher for camera feed
        self.publisher_ = self.create_publisher(Image, '/rover/camera/image_raw', 10)

        # OpenCV capture (OBSBOT camera at /dev/video0)
        self.cap = cv2.VideoCapture('/dev/video0')

        # Try setting resolution + MJPEG + FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 128)  
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 128)  
        self.cap.set(cv2.CAP_PROP_FPS, 20)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        if not self.cap.isOpened():
            self.get_logger().error(" Could not open /dev/video0 (OBSBOT Meet SE)")
        else:
            width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.get_logger().info(f"Opened OBSBOT Meet SE at {int(width)}x{int(height)} @ {int(fps)} FPS")

        self.bridge = CvBridge()

       
        self.timer = self.create_timer(1.0 / 20.0, self.timer_callback)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning("Failed to grab frame from OBSBOT camera")
            return

        # Convert BGR (OpenCV) to ROS2 Image
        msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        self.publisher_.publish(msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RoverCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

