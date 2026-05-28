import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

def generate_launch_description():
    # Setup project paths
    pkg_dream_world = get_package_share_directory('dream_world')
    pkg_rover_description = get_package_share_directory('rover_description')

    # Declare the launch arguments
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='basic_map.sdf',
        description='Name of the world file to load (e.g., basic_map.sdf or nxp_aim_india_2025/warehouse_2.sdf)'
    )

    # Path to the world file
    world_path = PathJoinSubstitution([
        pkg_dream_world,
        'worlds',
        LaunchConfiguration('world')
    ])

    # Direct execution of Gazebo Harmonic (gz sim)
    # This bypasses ros_gz_sim avoiding issues with Humble defaulting to Ignition Fortress
    gz_sim_launch = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        output='screen'
    )

    # Include the rover spawner launch file to bring in the URDF, bridges, and model spawner
    spawn_rover_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_rover_description, 'launch', 'spawn_rover.launch.py')
        )
    )

    return LaunchDescription([
        world_arg,
        gz_sim_launch,
        spawn_rover_launch
    ])
