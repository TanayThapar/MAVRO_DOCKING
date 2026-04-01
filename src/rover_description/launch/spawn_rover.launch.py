import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

# Calls:
# 1. Gazebo Ign
# 2. robot_state_publisher
# 3. spawned the bot
# 4. ros-gz bridge

def generate_launch_description():
    # Setup project paths
    pkg_rover_description = get_package_share_directory('rover_description')
    pkg_ros_ign_gazebo = get_package_share_directory('ros_ign_gazebo')

    urdf_path = os.path.join(pkg_rover_description, 'urdf', 'rover.urdf.xacro')
    bridge_config_path = os.path.join(pkg_rover_description, 'config', 'gz_bridge.yaml')
    world_path = os.path.join(pkg_rover_description, 'worlds', 'docking_world.sdf')

    # Ignition Gazebo
    ignition_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_ign_gazebo, 'launch', 'ign_gazebo.launch.py')
        ),
        launch_arguments={'ign_args': f'-r {world_path}'}.items()
    )

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
        package='ros_ign_gazebo',
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
        package='ros_ign_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config_path
        }],
        output='screen'
    )

    # 4. Aruco detector Node
    aruco_detector_node = Node(
        package='rover_description',
        executable='aruco_detector',
        name = 'aruco_detector',
        output='screen'
    )


    return LaunchDescription([
        ignition_gazebo,
        robot_state_publisher_node,
        spawn_rover_node,
        gz_bridge_node,
        aruco_detector_node
    ])
