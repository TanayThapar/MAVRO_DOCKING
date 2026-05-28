import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import json


class TwistToMotor(Node):
    def __init__(self):
        super().__init__('twist_to_motor')

        # Subscribe to /cmd_vel from teleop
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)

        # Publisher to /motor_cmds (to serial_bridge)
        self.motor_pub = self.create_publisher(String, '/motor_cmds', 10)

        # Parameters
        self.declare_parameter('max_speed', 500)     # motor speed scale
        self.declare_parameter('invert_right', True) # invert right side if wiring is reversed

        self.max_speed = self.get_parameter('max_speed').value
        self.invert_right = self.get_parameter('invert_right').value

    def cmd_vel_callback(self, msg: Twist):
        linear = msg.linear.x    # Forward/backward
        angular = msg.angular.z  # Left/right rotation

        # Tank drive: left/right wheel speeds
        left_speed = (linear - angular) * self.max_speed
        right_speed = (linear + angular) * self.max_speed

        # Invert right side if parameter set
        if self.invert_right:
            right_speed = -right_speed

        # Clamp speeds
        left_speed = int(max(min(left_speed, self.max_speed), -self.max_speed))
        right_speed = int(max(min(right_speed, self.max_speed), -self.max_speed))

        # Example: 4 hub motors (1,3 left side; 2,4 right side)
        commands = [
            {"T": 10010, "id": 2, "cmd": left_speed, "act": 3},
            {"T": 10010, "id": 4, "cmd": left_speed, "act": 3},
            {"T": 10010, "id": 3, "cmd": right_speed, "act": 3},
            {"T": 10010, "id": 1, "cmd": right_speed, "act": 3},
        ]

        # Publish JSON string
        msg_out = String()
        msg_out.data = "; ".join([json.dumps(c) for c in commands])
        self.motor_pub.publish(msg_out)

        self.get_logger().info(f"Published motor commands: {msg_out.data}")


def main(args=None):
    rclpy.init(args=args)
    node = TwistToMotor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
