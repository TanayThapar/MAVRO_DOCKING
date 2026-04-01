from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Joystick driver node
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
            parameters=[{'dev': '/dev/input/js0'}]  # Adjust if your PS5 shows up differently
        ),

        # Teleop twist node (maps joystick → /cmd_vel)
        Node(
            package='teleop_twist_joy',
            executable='teleop_node',
            name='teleop_twist_joy',
            output='screen',
            parameters=[{
                'axis_linear.x': 1,   # Left stick vertical
                'axis_angular.z': 0,  # Left stick horizontal
                'scale_linear.x': 1.0,
                'scale_angular.z': 1.0,
                'enable_button': 5    # R1 button to enable
            }]
        ),

        # Twist to motor converter node
        Node(
            package='motor_serial',
            executable='twist_to_motor',
            name='twist_to_motor',
            output='screen',
            parameters=[{'max_speed': 100}]
        ),

        # Serial bridge node
        Node(
            package='motor_serial',
            executable='serial_bridge',
            name='serial_bridge',
            output='screen',
            parameters=[{
                'port': '/dev/ttyACM0',   # adjust if your board is on ttyUSB0
                'baudrate': 115200
            }]
        ),
    ])

