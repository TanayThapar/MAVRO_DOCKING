import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # Alignment pid node
    aligning_pid_node = Node(
        package='rover_description',
        executable='dock_pid_controller',
        name='dock_pid_controller',
        output='screen'
    )

    # Docking pid node
    docking_pid_node = Node(
        package='rover_description',
        executable='dock_pid_controller_2',
        name='dock_pid_controller',
        output='screen'
    )

    return LaunchDescription([
        aligning_pid_node,
        docking_pid_node

    ])