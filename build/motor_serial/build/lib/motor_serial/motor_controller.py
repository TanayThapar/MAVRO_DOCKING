import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import serial

# Example: {"id":1, "cmd":50, "act":3}
#   id  -> motor ID
#   cmd -> speed / hex code / control value
#   act -> action (e.g. 3 = forward, 4 = reverse, etc.)


class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')
        
        # Subscriber to motor command topic
        self.subscriber = self.create_subscription(
            String, "/motor_cmd", self.listener_callback, 10
        )

        # Setup serial port (make sure same as in serial_bridge.py)
        try:
            self.ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
            self.get_logger().info("Serial connection established.")
        except Exception as e:
            self.get_logger().error(f"Serial connection failed: {e}")
            self.ser = None

    def listener_callback(self, msg):
        if not self.ser:
            self.get_logger().error("No serial connection.")
            return

        try:
            # Parse JSON input
            data = json.loads(msg.data)

            # Format motor command
            packet = json.dumps({
                "T": 10010,          # CMD_DDSM_CTRL
                "id": data["id"],    # Motor ID
                "cmd": data["cmd"],  # Speed/command
                "act": data["act"]   # Action
            }) + "\n"

            # Send to serial
            self.ser.write(packet.encode())
            self.get_logger().info(f"Sent: {packet.strip()}")

        except Exception as e:
            self.get_logger().error(f"Error processing command: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = MotorController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
