import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import threading
import json
import time


class SerialBridge(Node):
    def __init__(self):
        super().__init__('serial_bridge')

        # Parameters
        self.declare_parameter('port', '/dev/ttyAMA0')
        self.declare_parameter('baudrate', 115200)

        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value

        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=1)
            self.ser.setRTS(False)
            self.ser.setDTR(False)
            self.get_logger().info(f"Opened serial port {port} at {baudrate}")
        except Exception as e:
            self.get_logger().error(f"Failed to open serial: {e}")
            raise

        # ROS publishers/subscribers
        self.cmd_sub = self.create_subscription(
            String, 'motor_cmds', self.send_command, 10)
        self.feedback_pub = self.create_publisher(
            String, 'motor_feedback', 10)

        # Start thread to read serial feedback
        self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.serial_thread.start()

    def send_command(self, msg: String):
        commands = [c.strip() for c in msg.data.split(";") if c.strip()]
        for cmd in commands:
            try:
                json.loads(cmd)  # validate JSON
                self.ser.write((cmd + '\r\n').encode())
                self.ser.flush()
                self.get_logger().info(f"Sent: {cmd}")
                time.sleep(0.02)
            except json.JSONDecodeError:
                self.get_logger().warn(f"Invalid JSON skipped: {cmd}")

    def read_serial(self):
        while rclpy.ok():
            try:
                data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if data:
                    msg = String()
                    msg.data = data
                    self.feedback_pub.publish(msg)
            except Exception as e:
                self.get_logger().error(f"Serial read error: {e}")
                break
            time.sleep(0.01)  # avoid busy loop

    def destroy_node(self):
        if hasattr(self, "ser") and self.ser.is_open:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SerialBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
