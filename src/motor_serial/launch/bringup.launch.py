from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='motor_serial',
            executable='serial_bridge',
            name='serial_bridge',
            output='screen',
        ),
        Node(
            package='motor_serial',
            executable='twist_to_motor',
            name='twist_to_motor',
            output='screen',
        ),
        Node(
            package='motor_serial',
            executable='ps5_drive',
            name='ps5_drive',
            output='screen',
        ),
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
        ),
    ])
