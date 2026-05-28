import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():
    # Setup project paths
    pkg_rover_description = get_package_share_directory('rover_description')

    urdf_path = os.path.join(pkg_rover_description, 'urdf', 'rover.urdf.xacro')
    bridge_config_path = os.path.join(pkg_rover_description, 'config', 'gz_bridge.yaml')

    # 1. Robot State Publisher Node
    # Parses the xacro file and publishes the /robot_description topic and initial TF tree
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': Command(['xacro ', urdf_path])
        }],
        output='screen'
    )

    # 2. Spawn the Rover in Gazebo
    # Grabs the robot structure directly from the /robot_description topic to spawn it
    spawn_rover_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'rover',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.5' # Spawns slightly in the air so it drops into the world
        ],
        output='screen'
    )

    # 3. ROS <-> Gazebo Bridge
    # Uses the gz_bridge.yaml configuration we perfected earlier to route all the topics
    gz_bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config_path
        }],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher_node,
        spawn_rover_node,
        gz_bridge_node
    ])
