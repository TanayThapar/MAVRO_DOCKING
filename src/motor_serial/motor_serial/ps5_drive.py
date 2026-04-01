import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class PS5Drive(Node):
    def __init__(self):
        super().__init__('ps5_drive')

        # Subscribe to joystick input
        self.create_subscription(Joy, '/joy', self.joy_callback, 10)

        # Publish Twist messages for movement control
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Declare parameters for scaling
        self.declare_parameter('max_linear', 1.0)
        self.declare_parameter('max_angular', 1.0)
        self.max_linear = self.get_parameter('max_linear').value
        self.max_angular = self.get_parameter('max_angular').value

        # Initialize previous button and axis states
        self.prev_buttons = [0] * 16  # to store the previous state of buttons
        self.prev_axes = [0.0] * 6    # to store the previous state of axes

        # Log the startup
        self.get_logger().info("PS5 Drive Node started. R2 = forward, L2 = brake, Square + L2 = backward, Left/Right Joystick = rotate.")

    def joy_callback(self, msg: Joy):
        twist = Twist()

        try:
            # Initialize the linear and angular velocities to 0.0
            twist.linear.x = 0.0
            twist.angular.z = 0.0

            # Handle R2 (Forward movement) and L2 (Brake or backward) buttons
            if msg.buttons[7] == 1:  # R2 button pressed (forward)
                twist.linear.x = float(self.max_linear)
            elif msg.buttons[6] == 1:  # L2 button pressed
                if msg.buttons[0] == 1:  # Square button pressed (backward)
                    twist.linear.x = float(-self.max_linear)
                else:
                    twist.linear.x = 0.0  # L2 alone will brake (stop)

            # Handle Joystick movement (Rotation)
            twist.angular.z = float(msg.axes[0]) * self.max_angular  # Rotate left/right using left joystick

            # Stop rover immediately when button or joystick axis is released
            if msg.buttons[7] == 0 and self.prev_buttons[7] == 1:  # R2 released
                twist.linear.x = 0.0  # Stop rover
            if msg.buttons[6] == 0 and self.prev_buttons[6] == 1:  # L2 released
                twist.linear.x = 0.0  # Stop rover

            # Handle joystick release by checking axis for 0 value
            if abs(msg.axes[0]) < 0.05:  # If the joystick axis is close to neutral, stop rotation
                twist.angular.z = 0.0

            # Speed control using R1 and L1
            if msg.buttons[5] == 1:  # R1 button pressed (increase speed)
                self.max_linear += 0.1
                self.max_angular += 0.1
                self.get_logger().info(f"Max speed increased: {self.max_linear}, Max angular speed increased: {self.max_angular}")

            if msg.buttons[4] == 1:  # L1 button pressed (decrease speed)
                self.max_linear = max(0.1, self.max_linear - 0.1)
                self.max_angular = max(0.1, self.max_angular - 0.1)
                self.get_logger().info(f"Max speed decreased: {self.max_linear}, Max angular speed decreased: {self.max_angular}")

        except Exception as e:
            self.get_logger().error(f"Error in joy_callback: {str(e)}")

        # Log the velocities for debugging
        self.get_logger().info(f"Linear Velocity (x): {twist.linear.x}, Angular Velocity (z): {twist.angular.z}")

        # Publish the Twist message to /cmd_vel
        self.cmd_pub.publish(twist)

        # Save the current button and axis states for the next callback
        self.prev_buttons = list(msg.buttons)  # Convert to list before copying
        self.prev_axes = list(msg.axes)  # Convert to list before copying


def main(args=None):
    rclpy.init(args=args)
    node = PS5Drive()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
