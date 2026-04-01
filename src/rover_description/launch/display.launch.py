import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    urdf_path = os.path.join(
        get_package_share_directory('rover_description'),
        'urdf',
        'rover.urdf.xacro'
    )

    rviz_config_path = os.path.join(
        get_package_share_directory('rover_description'),
        'rviz',
        'rover_rviz_config.rviz'
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': Command(['xacro ', urdf_path])
        }],
        output='screen'
    )

    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path]
    )

    return LaunchDescription([
        # Uncomment if you want to run rviz indepently
        # robot_state_publisher_node,
        rviz2_node,
    ])