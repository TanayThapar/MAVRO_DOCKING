import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from pynput import keyboard

class ArrowTeleop(Node):
    def __init__(self):
        super().__init__('arrow_teleop')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.get_logger().info("Arrow Key Teleop started (↑↓←→)")

        self.speed = 0.5
        self.turn = 0.5

        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.daemon = True
        listener.start()

    def send_twist(self, linear_x, angular_z):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher.publish(msg)

    def on_press(self, key):
        try:
            if key == keyboard.Key.up:
                self.send_twist(self.speed, 0.0)
            elif key == keyboard.Key.down:
                self.send_twist(-self.speed, 0.0)
            elif key == keyboard.Key.left:
                self.send_twist(0.0, self.turn)
            elif key == keyboard.Key.right:
                self.send_twist(0.0, -self.turn)
        except Exception as e:
            self.get_logger().error(str(e))

    def on_release(self, key):
        # Stop when no key pressed
        self.send_twist(0.0, 0.0)

def main(args=None):
    rclpy.init(args=args)
    node = ArrowTeleop()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
